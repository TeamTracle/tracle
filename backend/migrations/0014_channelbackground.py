# Generated by Django 3.0.7 on 2021-01-03 10:57

import backend.fields
import backend.models
import backend.storage
import colorfield.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0013_channel_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChannelBackground',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desktop_image', backend.fields.WrappedImageField(storage=backend.storage.WrappedBCDNStorage(local_options={'base_url': backend.models.get_bg_image_media_url, 'location': backend.models.get_bg_image_base_location}), upload_to=backend.models.get_bg_image_location)),
                ('header_size', models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(150)])),
                ('imagemap', models.TextField(blank=True, max_length=5000, null=True)),
                ('color', colorfield.fields.ColorField(blank=True, default=None, max_length=18, null=True)),
                ('channel', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='background', to='backend.Channel')),
            ],
        ),
    ]
