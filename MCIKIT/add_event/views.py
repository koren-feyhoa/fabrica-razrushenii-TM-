from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, ListView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from .forms import EventForm
from .models import Event
from users.models import EventOrganizer

from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()

def add_event(request):
    return redirect('event_create')


class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    ordering = ['-event_date', '-event_time']


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_create.html'
    success_url = reverse_lazy('event_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Создаем запись организатора через модель EventOrganizer для создателя события
        EventOrganizer.objects.create(
            user=self.request.user,
            event=self.object,
            added_by=self.request.user
        )

        # Добавляем дополнительных организаторов
        additional_organizers = form.cleaned_data.get('additional_organizers', [])
        for organizer in additional_organizers:
            if organizer != self.request.user:  # Пропускаем, если организатор уже является создателем
                EventOrganizer.objects.create(
                    user=organizer,
                    event=self.object,
                    added_by=self.request.user
                )

        messages.success(self.request, 'Мероприятие успешно создано')
        return response

    def test_func(self):
        return self.request.user.is_pro_user()

    def form_valid(self, form):
        response = super().form_valid(form)
        # Создаем запись организатора через модель EventOrganizer
        EventOrganizer.objects.create(
            user=self.request.user,
            event=self.object,
            added_by=self.request.user
        )
        return response

    def test_func(self):
        return self.request.user.is_pro_user()


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    fields = ['title_event', 'description_Event',
              'event_place', 'event_date',
              'event_time', 'Event_photo',
              'max_members']
    template_name = 'events/event_update.html'
    success_url = reverse_lazy('event_list')
    context_object_name = 'event'

    def test_func(self):
        event = self.get_object()
        return event.is_user_organizer(self.request.user)


class EventParticipantsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Event
    template_name = 'events/event_participants.html'
    context_object_name = 'event'

    def test_func(self):
        event = self.get_object()
        return event.is_user_organizer(self.request.user)


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail_view.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        user = self.request.user

        # Определяем роль пользователя
        is_organizer = event.is_user_organizer(user)
        is_registered = event.is_user_registered(user)

        context.update({
            'is_organizer': is_organizer,
            'is_registered': is_registered,
            'registered_count': event.get_registered_count()
        })

        return context


@login_required
def event_register(request, pk):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=pk)
        if not event.is_user_registered(request.user):
            if event.max_members == 0 or event.get_registered_count() < event.max_members:
                event.users_members.add(request.user)
                messages.success(request, 'Вы успешно зарегистрировались на мероприятие')
            else:
                messages.error(request, 'Достигнуто максимальное количество участников')
        return redirect('event_detail', pk=pk)
    return HttpResponseForbidden()


@login_required
def event_unregister(request, pk):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=pk)
        if event.is_user_registered(request.user):
            event.users_members.remove(request.user)
            messages.success(request, 'Регистрация отменена')
        return redirect('event_detail', pk=pk)
    return HttpResponseForbidden()


@login_required
def event_delete(request, pk):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=pk)
        if event.is_user_organizer(request.user):
            event.delete()
            messages.success(request, 'Мероприятие успешно удалено')
            return redirect('event_list')
        return HttpResponseForbidden('У вас нет прав для удаления этого мероприятия')
    return HttpResponseForbidden()

def get_pro_users(request):
    """Возвращает список ProUser в формате JSON"""
    pro_users = User.objects.filter(role__in=['pro_user', 'super_user']).values('id', 'Name_User')
    return JsonResponse(list(pro_users), safe=False)