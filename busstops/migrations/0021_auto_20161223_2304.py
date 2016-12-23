# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-23 23:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('busstops', '0020_auto_20161124_2231'),
    ]

    operations = [
        migrations.AddField(
            model_name='operator',
            name='twitter',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AddField(
            model_name='service',
            name='inbound_description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='service',
            name='outbound_description',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='service',
            name='description',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]