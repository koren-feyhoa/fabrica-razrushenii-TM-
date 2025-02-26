# Generated by Django 5.1.6 on 2025-02-26 13:30

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('add_event', '0003_remove_event_rate_event_event_date_event_event_place_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='event_rate',
        ),
        migrations.AddField(
            model_name='event',
            name='event_time',
            field=models.TimeField(default=datetime.time(12, 0), verbose_name='Время начала'),
        ),
        migrations.AddField(
            model_name='event',
            name='max_members',
            field=models.PositiveIntegerField(blank=True, default=0, verbose_name='Максимальное количество участников'),
        ),
        migrations.AddField(
            model_name='event',
            name='prousers_members',
            field=models.ManyToManyField(related_name='Организаторы', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='users_members',
            field=models.ManyToManyField(related_name='Участники', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_date',
            field=models.DateField(verbose_name='Дата проведения мероприятия'),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_place',
            field=models.TextField(default=None, help_text='Место проведения мероприятия'),
        ),
        migrations.AlterField(
            model_name='event',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.CreateModel(
            name='EventRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='add_event.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_ratings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'event')},
            },
        ),
    ]
