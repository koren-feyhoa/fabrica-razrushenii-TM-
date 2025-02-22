#from django.contrib import admin
#from django.contrib.auth.admin import UserAdmin

#from .models import User, UserRoles

#admin.site.register(User, UserAdmin)
#admin.site.register(UserRoles)

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserRoles

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('Name_User', 'VK_id', 'Number_of_group', 'User_photo')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('Name_User', 'VK_id', 'Number_of_group', 'User_photo')}),
    )
    list_display = ('username', 'email', 'Name_User', 'Number_of_group', 'is_staff') #Добавляем поля для отображения в списке.

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserRoles)