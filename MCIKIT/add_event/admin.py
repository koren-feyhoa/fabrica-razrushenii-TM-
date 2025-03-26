from django.contrib import admin
from .models import Event, EventRating, ExtraInfo, Choice
from django.db.models import Avg

from users.admin import EventOrganizerInline

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1

class ExtraInfoInline(admin.TabularInline):
    model = ExtraInfo
    extra = 1
    inlines = [ChoiceInline]
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    inlines = [EventOrganizerInline,ExtraInfoInline]
    list_display = ('title_event', 'event_date', 'event_time', 'event_place')
    search_fields = ('title_event', 'description_Event')
    list_filter = ('event_date', 'event_place')
    fieldsets = (
        ('Event Details', {
            'fields': ('title_event', 'description_Event', 'event_date', 'event_time', 'event_place', 'Event_photo')
        }),
        ('Additional Settings', {
            'fields': ('max_members','users_members', 'registration_closed')
        }),
    )
    def average_rating(self, obj):
        result = obj.ratings.aggregate(avg_rating=Avg('rating'))
        return result['avg_rating'] or 0

    average_rating.short_description = 'Средний рейтинг'

admin.site.register(EventRating)
