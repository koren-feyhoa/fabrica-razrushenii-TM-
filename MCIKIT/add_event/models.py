from django.db import models
from datetime import datetime

class Event(models.Model):
    RATE_CHOICES = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    )
    id = models.AutoField(primary_key=True)
    title_event = models.TextField(help_text="Название мероприятия")
    description_Event = models.TextField(help_text="Описание мероприятия")
    event_rate = models.PositiveSmallIntegerField(default = None, choices=RATE_CHOICES) #доработать оценку
    event_place = models.TextField(default=None, help_text="Место проведеиня мероприятия")
    event_date = models.DateTimeField(default=datetime.now,verbose_name="Дата проведения мероприятия")
    Event_photo = models.ImageField(upload_to=None, height_field=None, width_field=None)
# Create your models here.
