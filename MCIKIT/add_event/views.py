from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, ListView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from .models import Event


def add_event(request):
    return redirect('event_create')


class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    ordering = ['-event_date', '-event_time']


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    fields = ['title_event', 'description_Event',
              'event_place', 'event_date',
              'event_time', 'Event_photo',
              'max_members']  # Fixed field name from max_member to max_members
    template_name = 'events/event_create.html'
    success_url = reverse_lazy('event_list')

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        response = super().form_valid(form)
        self.object.organizers.add(self.request.user)  # Add creator as organizer
        return response

    def test_func(self):
        return self.request.user.groups.filter(name='Активисты').exists()


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    fields = ['title_event', 'description_Event',
              'event_place', 'event_date',
              'event_time', 'Event_photo',
              'max_members']  # Fixed field name
    template_name = 'events/event_update.html'
    success_url = reverse_lazy('event_list')
    context_object_name = 'event'

    def test_func(self):
        event = self.get_object()
        return event.is_user_organizer(self.request.user)  # Using the model method


class EventParticipantsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Event
    template_name = 'events/event_participants.html' # Создайте шаблон events/event_participants.html
    context_object_name = 'event'

    def test_func(self):
        event = self.get_object()
        return event.organizer == self.request.user or self.request.user in event.authorized_editors.all() # Доступ только организатору и со-организаторам


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        user = self.request.user

        # Determine user role
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