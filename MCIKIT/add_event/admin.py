from django.contrib import admin
from .models import Event, EventRating
from django.db.models import Avg

class EventAdmin(admin.ModelAdmin):
    list_display = ('title_event', 'average_rating')

    def average_rating(self, obj):
        result = obj.ratings.aggregate(avg_rating=Avg('rating'))
        return result['avg_rating'] or 0

    average_rating.short_description = 'Средний рейтинг'

admin.site.register(Event, EventAdmin)
admin.site.register(EventRating)