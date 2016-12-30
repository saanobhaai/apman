# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-30 04:03
from __future__ import unicode_literals

from django.db import migrations, models

import satsound.models
import satsound.validators


class Migration(migrations.Migration):
    dependencies = [
        ('satsound', '0005_auto_20161229_0051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='satelliteaudio',
            name='audio',
            field=models.FileField(upload_to=satsound.models.satellite_upload,
                                   validators=[satsound.validators.validate_audio_size,
                                               satsound.validators.validate_audio_type]),
        ),
    ]
