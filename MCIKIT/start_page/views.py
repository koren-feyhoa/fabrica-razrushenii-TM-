from django.shortcuts import render, HttpResponse


def start_page(request):
    return render(request,'start_page/start_page.html')