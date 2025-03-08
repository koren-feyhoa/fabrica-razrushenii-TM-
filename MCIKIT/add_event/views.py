from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .models import Event


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    fields = ['title_event', 'description_Event',
              'event_place', 'event_date',
              'event_time', 'Event_photo',
              'max_member', 'prousers_members'
              ]  # Поля для формы создания мероприятия
    template_name = 'events/event_create.html'
    success_url = reverse_lazy('event_list')  # поменять

    def form_valid(self, form):
        form.instance.organizer = self.request.user  # Автоматически назначаем организатора -
        return super().form_valid(form)
    def test_func(self):
        return self.request.user.groups.filter(name='Активисты').exists()

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    fields = ['title_event', 'description_Event',
              'event_place', 'event_date',
              'event_time', 'Event_photo',
              'max_member', 'prousers_members'
              ]
    template_name = 'events/event_update.html'
    success_url = reverse_lazy('event_list')
    context_object_name = 'event'

    def test_func(self):
        event = self.get_object()
        return event.organizer == self.request.user or self.request.user in event.authorized_editors.all()  # Проверяем, является ли пользователь организатором или со-организатором
class EventParticipantsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Event
    template_name = 'events/event_participants.html' # Создайте шаблон events/event_participants.html
    context_object_name = 'event'

    def test_func(self):
        event = self.get_object()
        return event.organizer == self.request.user or self.request.user in event.authorized_editors.all() # Доступ только организатору и со-организаторам