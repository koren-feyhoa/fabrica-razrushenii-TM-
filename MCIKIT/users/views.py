from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect

from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework.reverse import reverse_lazy

from .forms import LoginUserForm

class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}


#def login_user(request):
#    if request.method=='POST':
#        form = LoginUserForm(request.POST)
#        if form.is_valid():
#            cd=form.cleaned_data
#            user=authenticate(request,username=cd['username'], password=cd['password'])
#            if user and user.is_active:
#                login(request,user)
#                return HttpResponseRedirect(reverse('start_page')) #Potom izmenit na main
#    else:
#        form = LoginUserForm()
#    return render(request, 'users/login.html', {'form': form})
#def logout_user(request):
#    logout(request)
#    return HttpResponseRedirect(reverse('users:login'))

