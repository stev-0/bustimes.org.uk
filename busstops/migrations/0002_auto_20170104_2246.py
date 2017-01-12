# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-04 22:46
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils.text import slugify


def forwards(apps, schema_editor):
    Locality = apps.get_model('busstops', 'Locality')
    Operator = apps.get_model('busstops', 'Operator')
    Service = apps.get_model('busstops', 'Service')
    db_alias = schema_editor.connection.alias
    for locality in Locality.objects.using(db_alias).all():
        locality.slug = slugify('{} {}'.format(locality.name, locality.qualifier_name))
        locality.save()
    for operator in Operator.objects.using(db_alias).all():
        operator.slug = slugify(operator.name)
        if len(operator.slug) > 50:
            print(operator)
            operator.slug = operator.slug[:50]
        operator.save()
    for service in Service.objects.using(db_alias).all():
        service.slug = slugify(' '.join(line_name, self.line_brand, self.description))
        if len(service.slug) > 50:
            print(service)
            service.slug = service.slug[:50]
        service.save()


class Migration(migrations.Migration):

    dependencies = [
        ('busstops', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='locality',
            name='slug',
            field=models.SlugField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='operator',
            name='slug',
            field=models.SlugField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='service',
            name='slug',
            field=models.SlugField(default=''),
            preserve_default=False,
        ),
        migrations.RunPython(forwards, elidable=True),
    ]
