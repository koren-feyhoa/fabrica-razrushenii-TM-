
from django.db import models
from datetime import datetime, time
from django.conf import settings
from django.db.models import ManyToManyField, Avg


class Event(models.Model):

    title_event = models.TextField(help_text="Название мероприятия")
    description_Event = models.TextField(help_text="Описание мероприятия")
    event_place = models.TextField(default=None, help_text="Место проведения мероприятия")
    event_date = models.DateField(blank=False,verbose_name="Дата проведения мероприятия")
    event_time=models.TimeField(blank=False, verbose_name="Время начала", default=time(12, 0))
    Event_photo = models.ImageField(upload_to=None, height_field=None, width_field=None)
    max_members=models.PositiveIntegerField(blank=True, verbose_name="Максимальное количество участников", default=0)
    users_members=ManyToManyField(settings.AUTH_USER_MODEL,related_name='Участники')
    prousers_members=ManyToManyField(settings.AUTH_USER_MODEL,related_name='Организаторы')

    def __str__(self):
        return self.title_event
    def average_rate(self):
        result = self.ratings.aggregate(avg_rating=Avg('rating'))
        return result['avg_rating'] or 0


class EventRating(models.Model):
    RATE_CHOICES = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_ratings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveSmallIntegerField(choices=RATE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event') # Один пользователь может оставить только одну оценку для мероприятия

    def __str__(self):
        return f"{self.user.Name_User} rated {self.event.title_event} with {self.rating}"
