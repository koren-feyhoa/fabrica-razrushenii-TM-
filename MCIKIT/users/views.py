from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, UpdateView
from rest_framework.reverse import reverse_lazy

from .forms import LoginUserForm, RegisterUserForm, UserSettingsForm
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


def UserSettingsView(request):
    user = request.user
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user.email = form.cleaned_data['email']
            user.Name_User = form.cleaned_data['Name_User']
            user.VK_id = form.cleaned_data['VK_id']
            user.Number_of_group = form.cleaned_data['Number_of_group']
            if 'Avatar' in request.FILES:
                user.Avatar = request.FILES['Avatar']
            user.save()
            return redirect('users:user_profile')
    else:
        form = UserSettingsForm(instance=user)
    return render(request, 'users/settings.html', {'form': form})