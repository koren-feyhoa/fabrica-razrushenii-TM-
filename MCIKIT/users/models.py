from django.db import models

class User(models.Model):
    # Id = models.AutoField(primary_key=True)
    Name_User=models.CharField(max_length=30,help_text="ФИО")
    Password=models.CharField(max_length=30,help_text='Пароль')
    Login=models.CharField(max_length=20, help_text='Логин')
    VK_id=models.CharField(max_length=30, help_text='id ВК')
    Number_of_events_attended=models.IntegerField() #Доделать логику
    Number_of_group=models.CharField(max_length=7, help_text="Номер группы")
    User_photo=models.ImageField(upload_to=None, height_field=None, width_field=None, blank=True)
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