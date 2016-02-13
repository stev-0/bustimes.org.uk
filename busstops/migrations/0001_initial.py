# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-26 14:40
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminArea',
            fields=[
                ('id', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('atco_code', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=48)),
                ('short_name', models.CharField(max_length=48)),
                ('country', models.CharField(max_length=3)),
            ],
        ),
        migrations.CreateModel(
            name='District',
            fields=[
                ('id', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=48)),
                ('admin_area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.AdminArea')),
            ],
        ),
        migrations.CreateModel(
            name='Locality',
            fields=[
                ('id', models.CharField(max_length=48, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=48)),
                ('qualifier_name', models.CharField(blank=True, max_length=48)),
                ('location', django.contrib.gis.db.models.fields.PointField(null=True, srid=27700)),
                ('adjancent', models.ManyToManyField(related_name='neighbour', to='busstops.Locality')),
                ('admin_area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.AdminArea')),
                ('district', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='busstops.District')),
                ('parent', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='busstops.Locality')),
            ],
        ),
        migrations.CreateModel(
            name='Operator',
            fields=[
                ('id', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('vehicle_mode', models.CharField(blank=True, max_length=48)),
                ('parent', models.CharField(blank=True, max_length=48)),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.CharField(max_length=2, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=48)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('service_code', models.CharField(max_length=24, primary_key=True, serialize=False)),
                ('line_name', models.CharField(max_length=64)),
                ('description', models.CharField(max_length=128)),
                ('mode', models.CharField(max_length=11)),
                ('net', models.CharField(blank=True, max_length=3)),
                ('date', models.DateField()),
                ('current', models.NullBooleanField(default=True)),
                ('operator', models.ManyToManyField(blank=True, to='busstops.Operator')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.Region')),
            ],
        ),
        migrations.CreateModel(
            name='StopArea',
            fields=[
                ('id', models.CharField(max_length=16, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=48)),
                ('stop_area_type', models.CharField(choices=[(b'GPBS', b'on-street pair'), (b'GCLS', b'on-street cluster'), (b'GAIR', b'airport building'), (b'GBCS', b'bus/coach station'), (b'GFTD', b'ferry terminal/dock'), (b'GTMU', b'tram/metro station'), (b'GRLS', b'rail station'), (b'GCCH', b'coach service coverage')], max_length=4)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=27700)),
                ('active', models.BooleanField()),
                ('admin_area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.AdminArea')),
                ('parent', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='busstops.StopArea')),
            ],
        ),
        migrations.CreateModel(
            name='StopPoint',
            fields=[
                ('atco_code', models.CharField(max_length=16, primary_key=True, serialize=False)),
                ('naptan_code', models.CharField(max_length=16)),
                ('common_name', models.CharField(max_length=48)),
                ('landmark', models.CharField(max_length=48)),
                ('street', models.CharField(max_length=48)),
                ('crossing', models.CharField(max_length=48)),
                ('indicator', models.CharField(max_length=48)),
                ('latlong', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('location', django.contrib.gis.db.models.fields.PointField(null=True, srid=27700)),
                ('suburb', models.CharField(max_length=48)),
                ('town', models.CharField(max_length=48)),
                ('locality_centre', models.BooleanField()),
                ('bearing', models.CharField(choices=[(b'N', b'north'), (b'NE', b'north east'), (b'E', b'east'), (b'SE', b'south east'), (b'S', b'south'), (b'SW', b'south west'), (b'W', b'west'), (b'NW', b'north west')], max_length=2)),
                ('stop_type', models.CharField(max_length=3)),
                ('bus_stop_type', models.CharField(max_length=3)),
                ('timing_status', models.CharField(max_length=3)),
                ('active', models.BooleanField(db_index=True)),
                ('admin_area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.AdminArea')),
                ('locality', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='busstops.Locality')),
                ('stop_area', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='busstops.StopArea')),
            ],
        ),
        migrations.AddField(
            model_name='service',
            name='stops',
            field=models.ManyToManyField(editable=False, to='busstops.StopPoint'),
        ),
        migrations.AddField(
            model_name='operator',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.Region'),
        ),
        migrations.AddField(
            model_name='adminarea',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.Region'),
        ),
    ]