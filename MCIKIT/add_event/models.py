from operator import truediv

from django.db import models
from datetime import datetime, time
from django.conf import settings
from django.db.models import ManyToManyField, Avg, ForeignKey, TextField, PositiveIntegerField
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
    registration_closed = models.BooleanField(default=False, verbose_name="Регистрация закрыта")
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
    likes = models.TextField(verbose_name="Что вам понравилось", blank=True, null=True)
    dislikes = models.TextField(verbose_name="Что вам не понравилось", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.Name_User} rated {self.event.title_event} with {self.rating}"

class ExtraInfo(models.Model):
    event=models.ForeignKey(Event,on_delete=models.CASCADE, related_name='extra_info')
    question = models.TextField(blank=True, null=True)
    field_type = models.CharField(max_length=50, choices=[
        ('text', 'Открытый вопрос'),
        ('choice', 'Вопрос с вариантами ответа'),
        ('team', 'Добавление команды'),
    ])
    choices = models.TextField(blank=True, null=True)
class UserAnswer(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='answers', null=True, blank=True)
    extra_info = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    choice = models.ForeignKey('Choice', on_delete=models.CASCADE, null=True, blank=True)
class Choice(models.Model):
    extra_info = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, related_name='choices_list')
    value = models.CharField(max_length=200)
