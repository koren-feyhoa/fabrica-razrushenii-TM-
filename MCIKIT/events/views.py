
from django.shortcuts import render, HttpResponse


def upcoming(request):
    return HttpResponse("<h1>Предстоящие мероприятия</h1>")
def made(request):
    return HttpResponse("<h1>Проведенные мероприятия</h1>")
