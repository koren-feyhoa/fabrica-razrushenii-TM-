# Generated by Django 5.1.6 on 2025-03-21 10:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('add_event', '0007_event_additional_questions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='additional_questions',
        ),
    ]
