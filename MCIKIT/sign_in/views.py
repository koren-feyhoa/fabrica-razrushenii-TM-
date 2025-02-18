from django.shortcuts import render

def sign_in(request):
    return render(request,'sign_in/sign_in.html')
