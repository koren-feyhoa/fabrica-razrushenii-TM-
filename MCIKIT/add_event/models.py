from django.db import models

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
    rate = models.PositiveSmallIntegerField(choices=RATE_CHOICES) #доработать оценку
    Event_photo = models.ImageField(upload_to=None, height_field=None, width_field=None)
# Create your models here.
