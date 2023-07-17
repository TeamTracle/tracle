import os

from django.conf import settings
from django.db.models import FileField
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator as token_generator

from backend import ffmpeg
from web.tokens import account_activation_token


def get_random_timestamps(duration):
    timestamps = []
    for x in range(3):
        timestamps.append(abs(((x + 1) - 0.5) * duration / 3))
    return timestamps


def get_video_duration(video):
    media_info = ffmpeg.ffprobe(
        video.uploaded_file.storage.local.path(video.uploaded_file.name)
    )
    return float(media_info["format"]["duration"])


def create_posters(video):
    duration = get_video_duration(video)
    timestamps = get_random_timestamps(duration)
    print(timestamps)
    posters = []
    for timestamp in timestamps:
        posters.append(
            ffmpeg.create_poster(
                video.uploaded_file.storage.local.path(video.uploaded_file.name),
                timestamp,
            )
        )
    return posters


def file_cleanup(sender, instance, **kwargs):
    """
    File cleanup callback used to emulate the old delete
    behavior using signals. Initially django deleted linked
    files when an object containing a File/ImageField was deleted.
    """

    for field in sender._meta.get_fields():
        if field and isinstance(field, FileField):
            fieldname = getattr(instance, field.name)

            if hasattr(fieldname, "path"):
                if os.path.exists(fieldname.path):
                    storage, path = fieldname.storage, fieldname.path
                    storage.delete(path)


def render_email_template(template_prefix, email, context, headers=None):
    to = [email]
    from_email = settings.DEFAULT_FROM_EMAIL

    subject = render_to_string(f"{template_prefix}_subject.txt", context)
    subject = " ".join(subject.splitlines()).strip()

    bodies = {}
    for ext in ["html", "txt"]:
        try:
            template_name = f"{template_prefix}_message.{ext}"
            bodies[ext] = render_to_string(template_name, context).strip()
        except TemplateDoesNotExist:
            if ext == "txt" and not bodies:
                # We need at least one body
                raise
    if "txt" in bodies:
        msg = EmailMultiAlternatives(
            subject, bodies["txt"], from_email, to, headers=headers
        )
        if "html" in bodies:
            msg.attach_alternative(bodies["html"], "text/html")
    else:
        msg = EmailMessage(subject, bodies["html"], from_email, to, headers=headers)
        msg.content_subtype = "html"  # Main content is now text/html
    return msg


def send_mail(template_prefix, email, context):
    msg = render_email_template(template_prefix, email, context)
    msg.send()


def get_mail_context(user):
    return {
        "user": user,
        "domain": settings.CURRENT_SITE["domain"],
        "protocol": settings.CURRENT_SITE["protocol"],
        "site_name": settings.CURRENT_SITE["name"],
    }


def send_confirmation_mail(user):
    context = get_mail_context(user)
    context["uid"] = urlsafe_base64_encode(force_bytes(user.pk))
    context["token"] = account_activation_token.make_token(user)
    send_mail("web/email/email_confirmation", user.email, context)


def send_password_reset_mail(user):
    context = get_mail_context(user)
    context["email"] = user.email
    context["uid"] = urlsafe_base64_encode(force_bytes(user.pk))
    context["token"] = token_generator.make_token(user)
    send_mail("web/email/password_reset_key", user.email, context)


def send_ban_notification_mail(user):
    context = get_mail_context(user)
    send_mail("web/email/ban_notification", user.email, context)


def send_videostrike_notification_mail(user, video):
    context = get_mail_context(user)
    context["video"] = video
    send_mail("web/email/videostrike_notification", user.email, context)
