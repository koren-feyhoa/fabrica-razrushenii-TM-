from django.shortcuts import render, HttpResponse


def sigh_in(request):
    return HttpResponse("<h1>Вход в учетную запись</h1>")
def log_in(request):
    return HttpResponse("<h1>Регистрация</h1>")
