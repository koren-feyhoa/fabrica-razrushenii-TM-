from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import inlineformset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, ListView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from .forms import EventForm, AnswerOptionForm, QuestionForm
from .models import Event, AnswerOption, UserAnswer, Question
from users.models import EventOrganizer, User

from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()


def add_event(request):
    return redirect('add_events:event_create')


class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    ordering = ['-event_date', '-event_time']


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_create.html'

    def get_success_url(self):
        from django.urls import reverse
        return reverse('add_events:event_detail_view', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        if not self.request.user.is_pro_user():
            messages.error(self.request, 'Только ProUser могут создавать мероприятия')
            return redirect('add_events:event_list')

        response = super().form_valid(form)
        event = self.object
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
        question_formset = inlineformset_factory(Event, Question, fields=('text',), extra=1, can_delete=True)(
            self.request.POST, instance=event, prefix='questions')

        if question_formset.is_valid():
            questions = question_formset.save(commit=False)
            for question in questions:
                if question.text:
                    question.event = event
                    question.save()
                    answer_formset = inlineformset_factory(Question, AnswerOption, fields=('text',), extra=2,
                                                           can_delete=True)(self.request.POST, instance=question,
                                                                            prefix=f'answers-{question.id}')
                    if answer_formset.is_valid():
                        answer_formset.save()

        messages.success(self.request, 'Мероприятие успешно создано')
        return response

    def test_func(self):
        return self.request.user.is_pro_user()


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_update.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        # Гарантируем, что event всегда есть в контексте
        context['event'] = event
        # Форматируем дату и время для HTML-инпутов
        context['event_date'] = event.event_date.strftime('%Y-%m-%d') if event.event_date else ''
        context['event_time'] = event.event_time.strftime('%H:%M') if event.event_time else ''
        return context

    def get_success_url(self):
        messages.success(self.request, 'Мероприятие успешно обновлено')
        return reverse_lazy('add_events:event_detail_view', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)

        event = self.object
        current_organizers = set(
            event.event_organizer_records.exclude(user=self.request.user).values_list('user', flat=True))
        new_organizers = set(form.cleaned_data.get('additional_organizers', []))

        for organizer_id in current_organizers - new_organizers:
            EventOrganizer.objects.filter(event=event, user_id=organizer_id).delete()

        for organizer_id in new_organizers - current_organizers:
            EventOrganizer.objects.create(
                user_id=organizer_id,
                event=event,
                added_by=self.request.user
            )
        question_formset = inlineformset_factory(Event, Question, fields=('text',), extra=1, can_delete=True)(
            self.request.POST, instance=event, prefix='questions')

        if question_formset.is_valid():
            questions = question_formset.save(commit=False)
            for question in questions:
                if question.text:
                    question.event = event
                    question.save()
                    answer_formset = inlineformset_factory(Question, AnswerOption, fields=('text',), extra=2,
                                                       can_delete=True)(self.request.POST, instance=question,
                                                                                prefix=f'answers-{question.id}')
                    if answer_formset.is_valid():
                        answer_formset.save()
        return response

    def test_func(self):
        event = self.get_object()
        if not event.is_user_organizer(self.request.user):
            messages.error(self.request, 'Только организаторы могут редактировать мероприятие')
            return False
        return True


class EventParticipantsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Event
    template_name = 'events/event_participants.html'
    context_object_name = 'event'

    def test_func(self):
        event = self.get_object()
        return event.is_user_organizer(self.request.user)

@login_required
def toggle_registration(request, pk):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=pk)
        if event.is_user_organizer(request.user):
            event.registration_closed = not event.registration_closed
            event.save()
            messages.success(request, 'Регистрация успешно ' + ('закрыта' if event.registration_closed else 'возобновлена'))
        else:
            messages.error(request, 'Только организаторы могут управлять регистрацией')
        return redirect('add_events:event_detail_view', pk=pk)
    return HttpResponseForbidden()

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
            'registered_count': event.get_registered_count(),
            'registration_closed': event.registration_closed
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
        return redirect('add_events:event_detail_view', pk=pk)
    return HttpResponseForbidden()


@login_required
def event_unregister(request, pk):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=pk)
        if event.is_user_registered(request.user):
            event.users_members.remove(request.user)
            messages.success(request, 'Регистрация отменена')
        return redirect('add_events:event_detail_view', pk=pk)
    return HttpResponseForbidden()


@login_required
def event_delete(request, pk):
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=pk)
        if event.is_user_organizer(request.user):
            event.delete()
            messages.success(request, 'Мероприятие успешно удалено')
            return redirect('add_events:event_list')
        return HttpResponseForbidden('У вас нет прав для удаления этого мероприятия')
    return HttpResponseForbidden()

def get_pro_users(request):
    """Возвращает список ProUser в формате JSON"""
    pro_users = User.objects.filter(role__in=['pro_user', 'super_user']).values('id', 'Name_User')
    return JsonResponse(list(pro_users), safe=False)


@login_required
def answer_questions(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    questions = event.questions.all()
    user = request.user

    if request.method == 'POST':
        if questions:  # Проверяем, есть ли вопросы
            all_questions_answered = True
            for question in questions:
                answer_id = request.POST.get(f'question_{question.id}')
                if answer_id:
                    answer = get_object_or_404(AnswerOption, pk=answer_id)
                    UserAnswer.objects.update_or_create(
                        user=user,
                        question=question,
                        defaults={'answer': answer}
                    )
                else:
                    all_questions_answered = False

            if all_questions_answered:
                event.users_members.add(user)
                return redirect('event_detail', pk=event_id)
            else:
                error_message = "Пожалуйста, ответьте на все вопросы."
                return render(request, 'answer_questions.html', {'event': event, 'questions': questions, 'error_message': error_message})
        else:  # Если вопросов нет, просто добавляем пользователя в участники
            event.users_members.add(user)
            return redirect('event_detail', pk=event_id)

    return render(request, 'answer_questions.html', {'event': event, 'questions': questions})

@login_required
def add_question(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    AnswerOptionFormSet = inlineformset_factory(Question, AnswerOption, form=AnswerOptionForm, extra=3)

    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        formset = AnswerOptionFormSet(request.POST)
        if question_form.is_valid() and formset.is_valid():
            question = question_form.save(commit=False)
            question.event = event
            question.save()
            formset.instance = question
            formset.save()
            return redirect('event_detail_view', pk=event_id)  # Замените 'event_detail' на URL вашего представления деталей события
    else:
        question_form = QuestionForm()
        formset = AnswerOptionFormSet()

    return render(request, 'events/add_question.html', {'question_form': question_form, 'formset': formset, 'event': event})

class EventReviewsView(DetailView):
    model = Event
    template_name = 'events/event_reviews.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        # Get all ratings for this event with related user information
        reviews = event.ratings.select_related('user').order_by('-timestamp')
        context['reviews'] = reviews
        return context