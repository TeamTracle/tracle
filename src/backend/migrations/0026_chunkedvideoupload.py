# Generated by Django 3.0.7 on 2021-12-31 02:03

import backend.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0025_auto_20210731_1350'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChunkedVideoUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload_id', models.CharField(default=uuid.uuid4, max_length=255, unique=True)),
                ('file', models.FileField(blank=True, max_length=255, null=True, upload_to=backend.models.generate_chunked_filename)),
                ('filename', models.CharField(default='untitled', max_length=255)),
                ('offset', models.BigIntegerField(default=0)),
                ('total_chunks', models.IntegerField(default=0)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created at')),
                ('completed', models.DateTimeField(blank=True, null=True, verbose_name='completed at')),
                ('status', models.CharField(choices=[('UP', 'Uploading'), ('CO', 'Complete'), ('AB', 'Aborted')], default='UP', max_length=2)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
