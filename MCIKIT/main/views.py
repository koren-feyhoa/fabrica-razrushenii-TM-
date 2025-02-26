
from django.shortcuts import render, HttpResponse


def main(request):
    return render(request, 'main_page.html')
