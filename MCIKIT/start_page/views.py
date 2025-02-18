from django.shortcuts import render, HttpResponse


def start_page(request):
    return HttpResponse("<h1>Начальная страница</h1>")