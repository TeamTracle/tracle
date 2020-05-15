import os, string, random, magic, base64, fixedint

from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from video_encoding.fields import VideoField
from video_encoding.models import Format

fs = FileSystemStorage(location=settings.TRACLE_UPLOAD_PATH)

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

class VideoFile(models.Model):
    width = models.PositiveIntegerField(editable=False, null=True)
    height = models.PositiveIntegerField(editable=False, null=True)
    duration = models.FloatField(editable=False, null=True)
    file = VideoField(width_field='width', height_field='height', duration_field='duration', storage=fs)
    format_set = GenericRelation(Format)
    processed = models.BooleanField(default=False)

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        if not magic.from_file(self.file.file.temporary_file_path(), mime=True).startswith('video/'):
            raise ValidationError('Unregocnized file format.')

    def __str__(self):
        return self.file.name

class Video(models.Model):

    class Visibility(models.TextChoices):
        PRIVATE = 'PRIVATE', 'Private'
        PUBLIC = 'PUBLIC', 'Public'
        UNLISTED = 'UNLISTED', 'Unlisted'

    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True ,null=True)
    watch_id = models.CharField(max_length=11, blank=True)
    visibility = models.CharField(max_length=8, choices=Visibility.choices, default=Visibility.PUBLIC)
    views = models.BigIntegerField(default=0)
    created = models.DateTimeField(default=timezone.now)
    thumbnail = models.ImageField(upload_to='thumbnails', blank=True)

    file = models.OneToOneField(VideoFile, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, blank=True, related_name='videos')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.title)

class Likes(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')

class Dislikes(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='dislikes')

class Subscription(models.Model):
    from_channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    to_channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='subscriptions')