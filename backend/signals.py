import base64, fixedint, re

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from actstream import action

from .models import Video, BunnyVideo, Channel, Image, Comment, Notification

@receiver(post_save, sender=Channel)
def generate_channel_id(sender, instance, **kwargs):
    if not instance.channel_id:
        instance.channel_id = base64.urlsafe_b64encode(fixedint.Int64(hash(str(instance.id+1))).to_bytes()).decode('UTF-8')[:-1]
        instance.save()

@receiver(post_save, sender=Video)
def generate_watch_id(sender, instance, created, **kwargs):
    if hasattr(instance, '_dirty'):
        return
    if not instance.watch_id:
        instance.watch_id = base64.urlsafe_b64encode(fixedint.Int64(hash(str(instance.id))).to_bytes()).decode('UTF-8')[:-1]
        try:
            instance._dirty = True
            instance.save()
        finally:
            del instance._dirty
    else:
        try:
            tvideo = instance.get_transcoded_video()
            if tvideo is None:
                return
            status = tvideo.status
            if not instance.subs_notified and instance.published and status == BunnyVideo.TranscodeStatus.DONE and instance.visibility == instance.VisibilityStatus.PUBLIC:
                action.send(instance.channel, verb='uploaded', action_object=instance)
                subs = [ sub.from_channel.user for sub in instance.channel.subscriptions.all() ]
                for sub in subs:
                    Notification.objects.create(notification_type=Notification.NotificationType.VIDEO, actor=instance.channel, action_object=instance, target_object=instance.channel, recipient=sub)
                instance.subs_notified = True
                try:
                    instance._dirty = True
                    instance.save()
                finally:
                    del instance._dirty
        except BunnyVideo.DoesNotExist:
            pass

@receiver(pre_delete, sender=Image)
def delete_image_files(sender, instance, using, **kwargs):
    instance.image.delete()

@receiver(pre_delete, sender=Video)
def delete_video_files(sender, instance, using, **kwargs):
    instance.delete_local_files()
    instance.delete_remote_files()

@receiver(pre_delete, sender=BunnyVideo)
def delete_bunnyvideo(sender, instance, using, **kwargs):
    instance.delete_files()

@receiver(post_save, sender=Comment)
def send_comment_notification(sender, instance, created, **kwargs):
    if created:
        action.send(instance.author, verb='commented', action_object=instance, target=instance.video)
        if instance.author != instance.video.channel:
            Notification.objects.create(notification_type=Notification.NotificationType.COMMENT, actor=instance.author, action_object=instance, target_object=instance.video, recipient=instance.video.channel.user)
        tags = re.findall('@\(\w+\)\[([aA-zZ0-9-_]+)\]', instance.text)
        if tags:
            for channel in Channel.objects.filter(channel_id__in=tags):
                if instance.author != channel:
                    Notification.objects.create(notification_type=Notification.NotificationType.TAG, actor=instance.author, action_object=instance, target_object=instance.video, recipient=channel.user)
