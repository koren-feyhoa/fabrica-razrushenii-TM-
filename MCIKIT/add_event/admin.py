from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Event

# Register your models here.

admin.site.register(Event)
