from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    USER_ROLES = (
        ('user', 'User'),
        ('pro_user', 'ProUser'),
        ('super_user', 'SuperUser'),
    )
    Name_User = models.CharField(max_length=30, verbose_name="ФИО")
    VK_id = models.CharField(max_length=30, verbose_name='ВК ID')
    Number_of_events_attended = models.IntegerField(default=0, verbose_name="Количество посещенных мероприятий")
    Number_of_group = models.CharField(max_length=30, verbose_name="Номер группы")
    Avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=10, choices=USER_ROLES, default='user', verbose_name="Роль пользователя")

    def is_pro_user(self):
        """Проверяет, является ли пользователь ProUser"""
        return self.role in ['pro_user', 'super_user']

    def is_super_user(self):
        """Проверяет, является ли пользователь SuperUser"""
        return self.role == 'super_user'

    def is_organizer_of_event(self, event):
        """Проверяет, является ли пользователь организатором конкретного мероприятия"""
        return self.event_organizers.filter(event=event).exists()

    def make_pro_user(self):
        """Повышает роль пользователя до pro-пользователя"""
        if not self.is_pro_user():
            self.role = 'pro_user'
            self.save()

    def make_organizer_of_event(self, event, added_by):
        """Делает пользователя организатором мероприятия"""
        if not self.is_pro_user():
            self.make_pro_user()
        if not self.is_organizer_of_event(event):
            EventOrganizer=apps.get_model('users', 'EventOrganizer') #izmenenie vozmozhno nuzhno ybrat
            EventOrganizer.objects.create(user=self, event=event, added_by=added_by)

    def get_organized_events(self):
        """Возвращает все мероприятия, где пользователь является организатором"""
        return [org.event for org in self.event_organizers.select_related('event').all()]

    def __str__(self):
        return f"{self.Name_User} | {self.Number_of_group}"


class EventOrganizer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_organizers')
    event = models.ForeignKey('add_event.Event', on_delete=models.CASCADE, related_name='event_organizer_records')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='added_organizers')
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')
        verbose_name = "Event Organizer"
        verbose_name_plural = "Event Organizers"

    def __str__(self):
        return f"{self.user.Name_User} - организатор {self.event.title_event}"