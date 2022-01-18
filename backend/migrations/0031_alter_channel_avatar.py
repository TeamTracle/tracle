# Generated by Django 3.2.11 on 2022-01-18 00:14

import backend.fields
import backend.models
import backend.storage
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0030_rename_thumbnail_new_image_thumbnail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='avatar',
            field=backend.fields.WrappedImageField(blank=True, null=True, storage=backend.storage.WrappedBCDNStorage(local_options={'base_url': backend.models.get_avatar_image_media_url, 'location': backend.models.get_avatar_image_base_location}), upload_to=backend.models.get_avatar_image_location),
        ),
    ]
