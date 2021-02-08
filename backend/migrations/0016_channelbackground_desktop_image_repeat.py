# Generated by Django 3.0.7 on 2021-01-09 00:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0015_add_trigram_extension'),
    ]

    operations = [
        migrations.AddField(
            model_name='channelbackground',
            name='desktop_image_repeat',
            field=models.CharField(choices=[('NR', 'no-repeat'), ('RE', 'repeat'), ('RX', 'repeat-x'), ('RY', 'repeat-y')], default='NR', max_length=2),
        ),
    ]