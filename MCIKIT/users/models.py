from django.db import models

class User(models.Model):
    Name_User=models.CharField(max_length=30,help_text="ФИО")
    Password=models.CharField(max_length=30,help_text='Пароль')
    Login=models.CharField(max_length=20, help_text='Логин')
    VK_id=models.CharField(max_length=30, help_text='id ВК')
    Number_of_events_attended=models.IntegerField() #Доделать логику
    Number_of_group=models.CharField(max_length=6, help_text="Номер группы")
    User_photo=models.ImageField(upload_to=None, height_field=None, width_field=None, blank=True)
    def __str__(self):
        return self.Name_User, self.Number_of_events_attended, self.Number_of_group, self.VK_id