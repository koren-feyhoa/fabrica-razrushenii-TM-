from django.db import models
from datetime import datetime, time
from django.conf import settings
from django.db.models import ManyToManyField, Avg
from django.template.context_processors import request
from django.apps import apps


class Event(models.Model):
    title_event = models.TextField(help_text="Название мероприятия")
    description_Event = models.TextField(help_text="Описание мероприятия")
    event_place = models.TextField(default=None, help_text="Место проведения мероприятия")
    event_date = models.DateField(blank=False, verbose_name="Дата проведения мероприятия")
    event_time = models.TimeField(blank=False, verbose_name="Время начала", default=time(12, 0))
    Event_photo = models.ImageField(upload_to=None, height_field=None, width_field=None)
    max_members = models.PositiveIntegerField(blank=True, verbose_name="Максимальное количество участников", default=0)
    users_members = ManyToManyField(settings.AUTH_USER_MODEL, related_name='event_members', blank=True)
    organizers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='users.EventOrganizer',
        through_fields=('event', 'user'),
        related_name='events_organized',
        blank=True
    )

    def __str__(self):
        return self.title_event

    def is_user_registered(self, user):
        """Проверяет, зарегистрирован ли пользователь на мероприятие"""
        return user in self.users_members.all()

    def is_user_organizer(self, user):
        """Проверяет, является ли пользователь организатором мероприятия"""
        if not user.is_authenticated:
            return False
        EventOrganizer = apps.get_model('users', 'EventOrganizer')
        return EventOrganizer.objects.filter(event=self, user=user).exists()

    def get_registered_count(self):
        """Возвращает количество зарегистрированных участников"""
        return self.users_members.count()

    def get_organizers(self):
        """Возвращает список всех организаторов мероприятия"""
        EventOrganizer = apps.get_model('users', 'EventOrganizer')
        return EventOrganizer.objects.filter(event=self).select_related('user')

    def add_organizer(self, user, added_by):
        """Добавляет нового организатора к мероприятию"""
        if not self.is_user_organizer(user):
            EventOrganizer = apps.get_model('users', 'EventOrganizer')
            EventOrganizer.objects.create(
                user=user,
                event=self,
                added_by=added_by
            )

    def remove_organizer(self, user):
        """Удаляет организатора из мероприятия"""
        EventOrganizer = apps.get_model('users', 'EventOrganizer')
        EventOrganizer.objects.filter(event=self, user=user).delete()

    def average_rate(self):
        """Возвращает среднюю оценку мероприятия"""
        result = self.ratings.aggregate(avg_rating=Avg('rating'))
        return result['avg_rating'] or 0

    class Meta:
        verbose_name = 'Мероприятие'


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
        unique_together = ('user', 'event')  # Один пользователь может оставить только одну оценку для мероприятия

    def __str__(self):
        return f"{self.user.Name_User} rated {self.event.title_event} with {self.rating}"