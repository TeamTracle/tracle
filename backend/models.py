import os, string, random, magic, base64, fixedint, json, shutil

from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

import django_rq
from django_rq.jobs import Job

from backend import bunnycdn

upload_fs = FileSystemStorage(location=settings.UPLOAD_ROOT)

def get_media_location(channel_id, watch_id):
    return os.path.join(settings.MEDIA_ROOT, channel_id, watch_id)

def get_upload_location(instance, filename):
    return os.path.join(instance.channel.channel_id, filename)

class UserManager(BaseUserManager):

    def create_user(self, email, password=None):
        if not email or not password:
            raise ValueError('Users must have email and password.')

        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        user.created = timezone.now()
        user.last_login = timezone.now()
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password=None):
        user = self.create_user(email, password=password)
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(email, password=password)
        user.admin = True
        user.staff = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    email = models.EmailField(max_length=255, unique=True)
    email_confirmed = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)
    created = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    @property
    def is_active(self):
        return self.active

    @property
    def is_staff(self):
        return self.staff

    @property
    def is_admin(self):
        return self.admin
    
    def __str__(self):
        return self.email

    def has_perm(self, app_label):
        return self.is_admin

    def has_module_perms(self, module):
        return self.is_admin

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

class Channel(models.Model):
    name = models.CharField(max_length=20)
    channel_id = models.CharField(max_length=11, editable=False, blank=True)
    created = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(blank=True, null=True)

    user = models.ForeignKey(User, related_name='channels', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.CharField(max_length=100)
    icon = models.CharField(max_length=100)

    def __str__(self):
        return str(self.title)

class Video(models.Model):

    class Visibility(models.TextChoices):
        PRIVATE = 'PRIVATE', 'Private'
        PUBLIC = 'PUBLIC', 'Public'
        UNLISTED = 'UNLISTED', 'Unlisted'

    class VideoStatus(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        DRAFT = 'draft', 'Draft'
        PROCESSING = 'started', 'Processing'
        DONE = 'finished', 'Done'
        ERROR = 'failed', 'Error'

    title = models.CharField(max_length=100, default='UNTITLED VIDEO')
    description = models.TextField(blank=True, null=True)
    watch_id = models.CharField(max_length=11, blank=True, null=True)
    visibility = models.CharField(max_length=8, choices=Visibility.choices, default=Visibility.PUBLIC)
    views = models.BigIntegerField(default=0)
    created = models.DateTimeField(default=timezone.now)
    uploaded_file = models.FileField(upload_to=get_upload_location, storage=upload_fs, null=True)
    thumbnail = models.CharField(max_length=255, null=True)
    video_status = models.CharField(max_length=255, choices=VideoStatus.choices, default=VideoStatus.DRAFT, db_column='video_status')
    job_id = models.CharField(max_length=255, null=True, blank=True)

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='videos')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=False)

    def __str__(self):
        return str('{}/{}'.format(self.channel.channel_id, self.watch_id))

    def get_thumbnail(self):
        if self.thumbnail:
            fsmedia = FileSystemStorage(location=get_media_location(self.channel.channel_id, self.watch_id))
            return fsmedia.url(os.path.join(self.channel.channel_id, self.watch_id, self.thumbnail))
        else:
            return ''

    def get_video_status(self):
        status = self.video_status
        try:
            job = Job.fetch(self.job_id, django_rq.get_connection())
            status = job.get_status()
            if status == 'queued':
                status = self.VideoStatus.QUEUED
            elif status == 'started':
                status = self.VideoStatus.PROCESSING
            elif status == 'finished':
                status == self.VideoStatus.DONE
            elif status == 'failed':
                status == self.VideoStatus.ERROR
        except:
            pass

        if not self.thumbnail:
            status = self.VideoStatus.DRAFT

        return status

    def get_url(self):
        if settings.BUNNYCDN.get('enabled'):
            return '{}/{}/{}/playlist.m3u8'.format(settings.BUNNYCDN['pullzone'], self.channel.channel_id, self.watch_id)
        else:
            return os.path.join(settings.MEDIA_URL, self.channel.channel_id, self.watch_id, 'playlist.m3u8')

    def get_media_fs(self):
        return FileSystemStorage(location=get_media_location(self.channel.channel_id, self.watch_id))

    def get_upload_fs(self):
        return FileSystemStorage(location=get_upload_location())

    def delete_files(self):
        bunnycdn.delete_file('{}/{}/'.format(self.channel.channel_id, self.watch_id))
        fs = self.get_media_fs()
        shutil.rmtree(fs.location)
        self.uploaded_file.delete()

class Likes(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')

class Dislikes(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='dislikes')

class Subscription(models.Model):
    from_channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    to_channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='subscriptions')