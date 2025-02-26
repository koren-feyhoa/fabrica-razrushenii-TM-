from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    Name_User=models.CharField(max_length=30, verbose_name="ФИО")
    VK_id=models.CharField(max_length=30, verbose_name='ВК ID')
    Number_of_events_attended=models.IntegerField(default=0, verbose_name="Количество посещенных мероприятий") #Доделать логику
    Number_of_group=models.CharField(max_length=7, verbose_name="Группа")
    User_photo=models.ImageField(upload_to="users/%Y/%m/%d/%user_id/", height_field=None, width_field=None, blank=True, null=True,verbose_name="Фоторгафия")
    def __str__(self):
        return f"{self.Name_User} | {self.Number_of_group}"

class UserRoles(models.Model):
    id= models.AutoField(primary_key=True)
    uuid = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Пользователь")
    isOrganizer = models.BooleanField()

    class Meta:
        verbose_name = "User role"
        ordering = ['id']

    def __str__(self):
        return f"<{self.id} | {self.uuid.Name_User} {self.uuid.Number_of_group}|" \
                f"isOrganizer::{self.isOrganizer}"
