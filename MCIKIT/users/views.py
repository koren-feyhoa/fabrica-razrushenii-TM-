from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, render
from django.views.generic import CreateView
from rest_framework.reverse import reverse_lazy

from .forms import LoginUserForm, RegisterUserForm
from .models import User


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': "Регистрация"}
    success_url = reverse_lazy('users:login')

@login_required
def profile(request):
    user = request
    return render(request, 'users/user_profile.html')