# Generated by Django 3.2.11 on 2022-02-11 07:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0031_alter_channel_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='imageset',
            name='custom_poster',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='backend.image'),
        ),
    ]
