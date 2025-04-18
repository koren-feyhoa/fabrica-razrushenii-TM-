# Generated by Django 5.1.6 on 2025-03-12 19:15

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_event', models.TextField(help_text='Название мероприятия')),
                ('description_Event', models.TextField(help_text='Описание мероприятия')),
                ('event_place', models.TextField(default=None, help_text='Место проведения мероприятия')),
                ('event_date', models.DateField(verbose_name='Дата проведения мероприятия')),
                ('event_time', models.TimeField(default=datetime.time(12, 0), verbose_name='Время начала')),
                ('Event_photo', models.ImageField(upload_to=None)),
                ('max_members', models.PositiveIntegerField(blank=True, default=0, verbose_name='Максимальное количество участников')),
            ],
            options={
                'verbose_name': 'Мероприятие',
            },
        ),
        migrations.CreateModel(
            name='EventRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
