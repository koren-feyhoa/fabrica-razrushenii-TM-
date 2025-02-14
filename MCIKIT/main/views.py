from http.client import HTTPResponse

from django.shortcuts import render


def main(request):
    return HTTPResponse("<h1>Главная страница</h1>")
