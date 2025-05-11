from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.generic import CreateView, UpdateView
from rest_framework.reverse import reverse_lazy

from .forms import LoginUserForm, RegisterUserForm, UserSettingsForm
from .models import User
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from add_event.models import EventRating, Event


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': "Регистрация"}
    success_url = reverse_lazy('users:login')

def personal(request):
    return render(request,'users/personal.html')

@login_required
def profile(request):
    user = request.user
    current_datetime = timezone.now()

    attended_events = Event.objects.filter(users_members=user).order_by('-event_date')
    attended_events_data = []

    for event in attended_events:
        event_data = {
            'event': event,
            'is_past': event.event_date < current_datetime.date() or (
                    event.event_date == current_datetime.date() and
                    event.event_time < current_datetime.time()
            ),
            'rating': EventRating.objects.filter(event=event, user=user).first()
        }
        attended_events_data.append(event_data)

    context = {
        'attended_events': attended_events_data,
    }

    if user.is_pro_user() or user.is_super_user():
        organized_events = Event.objects.filter(organizers=user).order_by('-event_date')
        context['organized_events'] = organized_events

    return render(request, 'users/user_profile.html', context)


@login_required
def rate_event(request, event_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    event = get_object_or_404(Event, id=event_id)
    current_datetime = timezone.now()
    event_datetime = timezone.make_aware(timezone.datetime.combine(event.event_date, event.event_time))

    if event_datetime > current_datetime:
        return JsonResponse({'error': 'Cannot rate future events'}, status=400)

    rating = request.POST.get('rating')
    likes = request.POST.get('likes', '')
    dislikes = request.POST.get('dislikes', '')

    if not rating or not rating.isdigit() or int(rating) not in range(1, 6):
        return JsonResponse({'error': 'Invalid rating value'}, status=400)

    event_rating, created = EventRating.objects.update_or_create(
        user=request.user,
        event=event,
        defaults={
            'rating': rating,
            'likes': likes,
            'dislikes': dislikes
        }
    )

    return JsonResponse({
        'success': True,
        'rating': event_rating.rating,
        'likes': event_rating.likes,
        'dislikes': event_rating.dislikes
    })


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
    user.make_pro_user()
    messages.success(request, f'Пользователь {user.Name_User} успешно повышен до ProUser')
    return redirect('users:user_list')

@login_required
def make_regular_user(request, user_id):
    """Понижает пользователя до обычного User"""
    if not request.user.is_super_user():
        raise PermissionDenied("Только SuperUser может понижать пользователей до User")

    user = get_object_or_404(User, id=user_id)
    user.make_regular_user()
    messages.success(request, f'Пользователь {user.Name_User} понижен до обычного пользователя')
    return redirect('users:user_list')