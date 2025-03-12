from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import CreateView, UpdateView
from rest_framework.reverse import reverse_lazy

from .forms import LoginUserForm, RegisterUserForm, UserSettingsForm
from .models import User
from django.core.exceptions import PermissionDenied
from django.contrib import messages


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
            user.VK_id = form.cleaned_data['VK_id']
            user.Number_of_group = form.cleaned_data['Number_of_group']
            if 'Avatar' in request.FILES:
                user.Avatar = request.FILES['Avatar']
            user.save()
            return redirect('users:user_profile')
    else:
        form = UserSettingsForm(instance=user)
    return render(request, 'users/settings.html', {'form': form})


@login_required
def user_list(request):
    """Отображает список пользователей"""
    if not request.user.is_super_user():
        raise PermissionDenied("Только SuperUser может просматривать список пользователей")

    users = User.objects.exclude(role='super_user').order_by('username')
    return render(request, 'users/user_list.html', {'users': users})


@login_required
def make_pro_user(request, user_id):
    """Повышает пользователя до ProUser"""
    if not request.user.is_super_user():
        raise PermissionDenied("Только SuperUser может повышать пользователей до ProUser")

    user = get_object_or_404(User, id=user_id)
    user.make_pro_user(promoted_by=request.user)
    messages.success(request, f'Пользователь {user.Name_User} успешно повышен до ProUser')
    return redirect('user_list')