from datetime import timedelta
import os, string, random, magic, base64, fixedint, json, shutil
import re
import uuid
import hashlib
import time

from django.core.exceptions import FieldError
from django.core.files.storage import FileSystemStorage
from django.core.files.base import File
from django.core.files.uploadedfile import UploadedFile
from django.core.mail import send_mail
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

import django_rq
from django_rq.jobs import Job

from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFill

import bleach

from colorfield.fields import ColorField

from .storage import WrappedBCDNStorage
from .fields import WrappedFileField, WrappedImageField
from .managers import UserManager, VideoManager
from . import tasks, utils
from bunnyapi import VideosApi

def get_video_location(instance, filename=None):
    if instance.pk is None:
        raise FieldError('Model instance does not have a pk.')

    if filename:
        return f'{instance.channel.channel_id}/{instance.watch_id}/{filename}'
    else:
        return f'{instance.channel.channel_id}/{instance.watch_id}/'

def get_playlist_location(instance, filename=None):
    if filename:
        return f'{instance.video.channel.channel_id}/{instance.video.watch_id}/{filename}'
    else:
        return f'{instance.video.channel.channel_id}/{instance.video.watch_id}/'


def get_image_location(instance, filename=None):
    if filename:
        return f'{instance.video.channel.channel_id}/{instance.video.watch_id}/{filename}'
    else:
        return f'{instance.video.channel.channel_id}/{instance.video.watch_id}/'

def get_bg_image_location(instance, filename=None):
    if filename:
        return f'{instance.channel.channel_id}/{filename}'
    else:
        return f'{instance.channel.channel_id}/'

def get_bg_image_media_url():
    return os.path.join(settings.MEDIA_URL, 'backgrounds')

def get_bg_image_base_location():
    return os.path.join(settings.MEDIA_ROOT, 'backgrounds')

def get_poster_media_url():
    return os.path.join(settings.MEDIA_URL, 'posters')

def get_poster_base_location():
    return os.path.join(settings.MEDIA_ROOT, 'posters')

def get_video_base_location():
    return os.path.join(settings.MEDIA_ROOT, 'videos')

def get_video_media_url():
    return os.path.join(settings.MEDIA_URL, 'videos')

class User(PermissionsMixin, AbstractBaseUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    email = models.EmailField(max_length=255, unique=True)
    email_confirmed = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)
    banned_at = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    notes = models.TextField(default='', blank=True)
    ipadress = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    @property
    def is_active(self):
        return self.active

    @property
    def is_staff(self):
        return self.staff

    def __str__(self):
        return self.email

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def update_last_login(self, ipadress):
        self.last_login = timezone.now()
        self.ipadress = ipadress
        self.save()

class Channel(models.Model):
    name = models.CharField(max_length=20)
    description = models.TextField(max_length=5000, default="")
    channel_id = models.CharField(max_length=11, editable=False, blank=True)
    created = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(blank=True, null=True)
    verified = models.BooleanField(default=False)

    user = models.ForeignKey(User, related_name='channels', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def update_last_login(self):
        self.last_login = timezone.now()
        self.save()

    def get_avatar(self):
        if self.avatar:
            return self.avatar.url
        return '/static/web/img/avatar.png'

class ChannelBackground(models.Model):
    class RepeatChoices(models.TextChoices):
        NO_REPEAT = 'NR', 'no-repeat'
        REPEAT = 'RE', 'repeat'
        REPEAT_X = 'RX', 'repeat-x'
        REPEAT_Y = 'RY', 'repeat-y'

    channel = models.OneToOneField(Channel, on_delete=models.CASCADE, related_name='background')
    desktop_image = WrappedImageField(storage=WrappedBCDNStorage(local_options={'location' : get_bg_image_base_location, 'base_url' : get_bg_image_media_url}), upload_to=get_bg_image_location)
    desktop_image_repeat = models.CharField(max_length=2, choices=RepeatChoices.choices, default=RepeatChoices.NO_REPEAT, blank=True)
    header_size = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(150)])
    imagemap = models.TextField(max_length=5000, null=True, blank=True)
    color = ColorField(default="#CCCCCC", blank=True)

    def get_map_code(self):
        if self.imagemap and self.header_size > 0:
            return bleach.clean(self.imagemap, tags=['area'], attributes={'area' : ['shape', 'coords', 'alt', 'href', 'target']}, strip=True).strip()
        else:
            return ''

class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)
    icon = models.CharField(max_length=100)

    def __str__(self):
        return str(self.title)

class ImageSet(models.Model):
    primary_image = models.ForeignKey('Image', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)

    def image_data(self):
        return {
            "pk": self.pk,
            "primaryImage": self.primary_image.data() if self.primary_image else {},
            "images": [image.data() for image in self.images.all()],
        }

    def transfer(self):
        for img in self.images.all():
            img.image.storage.transfer(img.image.name)
            img.thumbnail.storage.transfer(img.thumbnail.name)
        self.delete_local_files()

    def delete_local_files(self):
        folder = os.path.join(get_poster_base_location(), get_image_location(self))
        if os.path.exists(folder):
            shutil.rmtree(folder)


class Image(models.Model):
    image = WrappedImageField(storage=WrappedBCDNStorage(local_options={'location' : get_poster_base_location, 'base_url' : get_poster_media_url}), upload_to=get_image_location)
    created_at = models.DateTimeField(default=timezone.now)

    image_set = models.ForeignKey(ImageSet, related_name="images", on_delete=models.CASCADE)
    video = models.ForeignKey('Video', related_name="images", on_delete=models.CASCADE)

    thumbnail = ProcessedImageField(null=True, processors=[ResizeToFill(320, 180)], format='PNG', storage=WrappedBCDNStorage(local_options={'location' : get_poster_base_location, 'base_url' : get_poster_media_url}), upload_to=get_image_location)

    def toggle_primary(self):
        if self.image_set.primary_image == self:
            return
        else:
            self.image_set.primary_image = self
        self.image_set.save()

    def data(self):
        return {
            "pk": self.pk,
            "is_primary": self == self.image_set.primary_image,
            "thumbnail": self.thumbnail.url,
        }

class BunnyVideo(models.Model):
    class TranscodeStatus(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        PROCESSING = 'started', 'Processing'
        DONE = 'finished', 'Done'
        ERROR = 'failed', 'Error'

    status = models.CharField(max_length=255, choices=TranscodeStatus.choices, default=TranscodeStatus.QUEUED)
    bunny_guid = models.CharField(max_length=255, null=True, blank=True)
    video = models.OneToOneField('Video', on_delete=models.CASCADE)

    def upload(self):
        django_rq.enqueue(tasks.bunnyvideo_upload_task, bunny_video=self)

    def get_playlist(self):
        return f'{settings.BUNNYNET["storage_url"]}/{self.bunny_guid}/playlist.m3u8'

    def get_preview(self):
        return f'{settings.BUNNYNET["storage_url"]}/{self.bunny_guid}/preview.webp'

    def delete_files(self):
        vapi = VideosApi(settings.BUNNYNET['access_token'], settings.BUNNYNET['library_id'])
        vapi.delete_video(self.bunny_guid)

def generate_chunked_filename(instance, filename):
    ext = '.part'
    ext += os.path.splitext(filename)[1]

    filename = os.path.join(instance.upload_dir, str(instance.upload_id) + '.upload')
    return time.strftime(filename)

def generate_chunk_filename(instance, chunk_number):
    return os.path.join(settings.MEDIA_ROOT, instance.upload_dir, str(instance.upload_id), str(chunk_number) + '.part')

class ChunkedVideoUpload(models.Model):
    upload_dir = 'chunked_uploads'

    class UploadStatus(models.TextChoices):
        UPLOADING = 'UP', 'Uploading'
        COMPLETE = 'CO', 'Complete'
        ABORTED = 'AB', 'Aborted'

    upload_id = models.CharField(max_length=255, default=uuid.uuid4, unique=True)
    file = models.FileField(upload_to=generate_chunked_filename, max_length=255, null=True, blank=True)
    filename = models.CharField(max_length=255, default='untitled') #TODO: REMOVE
    offset = models.BigIntegerField(default=0)
    total_chunks = models.IntegerField(default=0)
    created = models.DateTimeField(verbose_name=('created at'), default=timezone.now, editable=False)
    completed = models.DateTimeField(verbose_name=('completed at'), null=True, blank=True)
    status = models.CharField(max_length=2, choices=UploadStatus.choices, default=UploadStatus.UPLOADING)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def expires_at(self):
        return self.created + timedelta(days=1)

    @property
    def expired(self):
        return self.expires_at <= timezone.now()

    def delete_file(self):
        if self.file:
            storage, path = self.file.storage, self.file.path
            storage.delete(path)
        self.file = None

    @transaction.atomic
    def delete(self, delete_file=True, *args, **kwargs):
        super(ChunkedVideoUpload, self).delete(*args, **kwargs)
        if delete_file:
            self.delete_file()

    def concat_chunks(self):
        f = open(os.path.join(settings.MEDIA_ROOT, self.upload_dir, str(self.upload_id), '1.part'), 'rb')
        self.file.save('cskaljdskajdk.mp4', File(f))
        f.close()
        for chunk_number in range(2, self.total_chunks+1):
            f = open(os.path.join(settings.MEDIA_ROOT, self.upload_dir, str(self.upload_id), str(chunk_number)+'.part'), 'rb')
            chunk = UploadedFile(file=f)
            self.append_chunk(chunk, save=False)
            f.close()
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, self.upload_dir, self.upload_id))

    def append_chunk(self, chunk, save=True):
        self.file.close()
        self.file.open(mode='ab')  # mode = append+binary
        for subchunk in chunk.chunks():
            self.file.write(subchunk)
        self._md5 = None  # Clear cached md5
        if save:
            self.save()
        self.file.close()  # Flush

    def save_chunk(self, chunk, chunk_number, total_chunks):
        filename = generate_chunk_filename(self, chunk_number)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, self.upload_dir, str(self.upload_id)), exist_ok=True)
        with open(filename, 'wb') as f:
            for c in chunk.chunks():
                f.write(c)
        if self.total_chunks == 0:
            self.total_chunks = total_chunks
        self.save()

    @transaction.atomic
    def set_completed(self, completed_at=timezone.now()):
        self.concat_chunks()
        self.status = self.UploadStatus.COMPLETE
        self.completed_at = completed_at
        self.save()

@receiver(post_delete, sender=ChunkedVideoUpload)
def auto_file_cleanup(sender, instance, **kwargs):
    utils.file_cleanup(sender, instance, **kwargs)

class Video(models.Model):

    class VisibilityStatus(models.TextChoices):
        PRIVATE = 'PRIVATE', 'Private'
        PUBLIC = 'PUBLIC', 'Public'
        UNLISTED = 'UNLISTED', 'Unlisted'
        DRAFT = 'draft', 'Draft'

    title = models.CharField(max_length=100, default='UNTITLED VIDEO')
    description = models.TextField(blank=True, null=True)
    watch_id = models.CharField(max_length=11, blank=True, null=True)
    created = models.DateTimeField(default=timezone.now)

    uploaded_file = WrappedFileField(max_length=255, storage=WrappedBCDNStorage(local_options={'location' : get_video_base_location, 'base_url' : get_video_media_url}), upload_to=get_video_location, blank=True)
    image_set = models.OneToOneField(ImageSet, on_delete=models.CASCADE, null=True)

    visibility = models.CharField(max_length=8, choices=VisibilityStatus.choices, default=VisibilityStatus.PRIVATE)
    published = models.BooleanField(default=False)
    
    views = models.BigIntegerField(default=0)

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='videos')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=False)

    objects = VideoManager()

    subs_notified = models.BooleanField(default=False)
    action_relations = GenericRelation('Notification', object_id_field='action_id', content_type_field='action_type')
    target_relations = GenericRelation('Notification', object_id_field='target_id', content_type_field='target_type')

    def __str__(self):
        return str('{}/{}'.format(self.channel.channel_id, self.watch_id))

    def transcode(self):
        bvideo = BunnyVideo.objects.create(video=self)
        bvideo.upload()

    def get_transcoded_video(self):
        try:
            self.bunnyvideo.status
            return self.bunnyvideo
        except BunnyVideo.DoesNotExist:
            return None

    def get_playlist(self):
        return self.bunnyvideo.get_playlist()

    def create_posters(self):
        if self.image_set:
            for img in self.image_set.images.all():
                img.delete()
        else:
            self.image_set = ImageSet.objects.create()
            self.save()
        poster_files = utils.create_posters(self)
        for f in poster_files:
            img = Image.objects.create(image_set=self.image_set, video=self)
            img.image.save('poster.png', File(open(f, 'rb')))
            img.thumbnail.save('thumbnail.png', File(open(f, 'rb')))
        img.toggle_primary()
        self.image_set.transfer()

    def get_poster(self):
        if self.image_set and self.image_set.primary_image and self.image_set.primary_image.image and self.image_set.primary_image.image.storage.exists(self.image_set.primary_image.image.name):
            return self.image_set.primary_image.image.url
        else:
            return ''

    def get_thumbnail(self):
        if self.image_set and self.image_set.primary_image and self.image_set.primary_image.thumbnail and self.image_set.primary_image.thumbnail.storage.exists(self.image_set.primary_image.thumbnail.name):
            return self.image_set.primary_image.thumbnail.url
        else:
            return '/static/web/img/thumbnail_default.jpg'

    def get_preview(self):
        return self.bunnyvideo.get_preview()

    def transfer_files(self):
        folder = os.path.join(get_video_base_location(), get_video_location(self))
        for f in os.listdir(folder):
            f = get_video_location(self, filename=f)
            self.uploaded_file.storage.transfer(f)
        self.delete_local_files()

    def delete_local_files(self):
        folder = os.path.join(get_video_base_location(), get_video_location(self))
        if os.path.exists(folder):
            shutil.rmtree(folder)

    def delete_remote_files(self):
        folder = get_video_location(self)
        self.uploaded_file.storage.remote.delete(folder)

class Likes(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')

class Dislikes(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='dislikes')

class Subscription(models.Model):
    from_channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='subscribers')
    to_channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='subscriptions')

class Comment(models.Model):
    author = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='comments')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField(max_length=500)
    created = models.DateTimeField(default=timezone.now)

    action_relations = GenericRelation('Notification', object_id_field='action_id', content_type_field='action_type')
    target_relations = GenericRelation('Notification', object_id_field='target_id', content_type_field='target_type')

    def sanitized_text(self):
        return bleach.clean(self.text, tags=[])

    def __str__(self):
        return f'Comment from {self.author.name} on {self.video.title}'

class CommentLike(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')

class CommentDislike(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='dislikes')

class TicketManager(models.Manager):
    def is_open(self):
        return super().get_queryset().filter(status=Ticket.Status.OPEN)

    def is_closed(self):
        return super().get_queryset().filter(status=Ticket.Status.CLOSED)

class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OP', 'Open'
        CLOSED = 'CL', 'Closed'

    class Reason(models.TextChoices):
        SPAM = 'SP', 'Unwanted commercial content or spam'
        PORN = 'PO', 'Pornography or sexually explicit material'
        CHILDE_ABUSE = 'CA', 'Child abuse'
        HATE_OR_VIOLENCE = 'HV', 'Hate speech or graphic violence'
        HARASEMENT_OR_BULLYING = 'HB', 'Harassment or bullying'

    status = models.CharField(max_length=2, choices=Status.choices, default=Status.OPEN)
    reason = models.CharField(max_length=2, choices=Reason.choices)

    objects = TicketManager()
    
class CommentTicket(Ticket):
    channel = models.ForeignKey(Channel, null=True, on_delete=models.SET_NULL)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    body = models.TextField(max_length=500, blank=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.channel} reported Comment {self.comment.pk}'

class VideoTicket(Ticket):
    channel = models.ForeignKey(Channel, null=True, on_delete=models.SET_NULL)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    body = models.TextField(max_length=500, blank=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.channel} reported Video {self.video.watch_id}'

class NotificationManager(models.Manager):
    def unread(self):
        return super().get_queryset().filter(unread=True)

class Notification(models.Model):
    class Meta:
        ordering = ('-created',)

    class NotificationType(models.TextChoices):
        COMMENT = 'CO', 'New Comment'
        TAG = 'TA', 'Tagged User'
        VIDEO = 'VI', 'New Video'

    notification_type = models.CharField(max_length=2, choices=NotificationType.choices)
    created = models.DateTimeField(default=timezone.now)
    unread = models.BooleanField(default=True)

    actor = models.ForeignKey(Channel, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')

    action_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='actions')
    action_id = models.PositiveIntegerField()
    action_object = GenericForeignKey('action_type', 'action_id')

    target_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='targets')
    target_id  = models.PositiveIntegerField()
    target_object = GenericForeignKey('target_type', 'target_id')

    objects = NotificationManager()

class WatchHistoryManager(models.Manager):
    def add_entry(self, channel, video):
        try:
            entry = self.get(channel=channel, video=video)
            entry.created = timezone.now()
            entry.save()
        except WatchHistory.DoesNotExist:
            self.create(channel=channel, video=video)

class WatchHistory(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='watch_history')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='+')
    created = models.DateTimeField(default=timezone.now)

    objects = WatchHistoryManager()

class Strike(models.Model):
    class CategoryChoices(models.TextChoices):
        COPYRIGHT = 'CY', 'Copyright'
        COMMUNITY = 'CG', 'Community Guidelines'

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now)
    category = models.CharField(max_length=2, choices=CategoryChoices.choices)

    class Meta:
        abstract = True

class VideoStrike(Strike):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, blank=True, null=True)

class CommentStrike(Strike):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True)
