import base64, fixedint

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files import File
from django_rq import enqueue

from video_encoding import tasks

from .models import VideoFile, Video, Channel

@receiver(post_save, sender=Channel)
def generate_channel_id(sender, instance, **kwargs):
    if not instance.channel_id:
        instance.channel_id = base64.urlsafe_b64encode(fixedint.Int64(hash(str(instance.id))).to_bytes()).decode('UTF-8')[:-1]
        instance.save()

@receiver(post_save, sender=Video)
def generate_watch_id(sender, instance, created, **kwargs):
    if not instance.watch_id:
        instance.watch_id = base64.urlsafe_b64encode(fixedint.Int64(hash(str(instance.id))).to_bytes()).decode('UTF-8')[:-1]
        instance.save()

@receiver(post_save, sender=VideoFile)
def convert_video(sender, instance, **kwargs):
    enqueue(tasks.convert_all_videos,
            instance._meta.app_label,
            instance._meta.model_name,
            instance.pk)