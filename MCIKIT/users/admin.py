#from django.contrib import admin
#from django.contrib.auth.admin import UserAdmin

#from .models import User, UserRoles

#admin.site.register(User, UserAdmin)
#admin.site.register(UserRoles)

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, EventOrganizer



class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'Name_User', 'Number_of_group', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'Name_User', 'Number_of_group')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('Name_User', 'Number_of_group', 'VK_id', 'Avatar')}),
        ('Права доступа', {'fields': ('role', 'is_active')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'Name_User', 'Number_of_group', 'VK_id', 'role'),
        }),
    )

    def get_readonly_fields(self, request, obj=None): #Делаем поле role доступным только для суперпользователей
        if not request.user.is_superuser:
            return self.readonly_fields + ('role',)
        return self.readonly_fields

class EventOrganizerAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'added_by', 'date_added')
    list_filter = ('date_added',)
    search_fields = ('user__Name_User', 'event__title_event', 'added_by__Name_User')
    raw_id_fields = ('user', 'event', 'added_by')
class EventOrganizerInline(admin.TabularInline):
    model = EventOrganizer
    extra = 1


admin.site.register(User, CustomUserAdmin)
admin.site.register(EventOrganizer, EventOrganizerAdmin)


