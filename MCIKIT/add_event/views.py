from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import inlineformset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, ListView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import Q
from django.db import transaction

from .forms import EventForm, ExtraInfoForm, ChoiceForm, UserAnswerForm
from .models import Event, ExtraInfo, Choice, UserAnswer
from users.models import EventOrganizer, User


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

        try:
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

            # Обрабатываем открытые вопросы
            open_questions = {}
            for key, value in self.request.POST.items():
                if key.startswith('open_questions'):
                    parts = key.split('[')
                    index = int(parts[1].split(']')[0])
                    field = parts[2].split(']')[0]
                    if index not in open_questions:
                        open_questions[index] = {}
                    open_questions[index][field] = value

            for question_data in open_questions.values():
                ExtraInfo.objects.create(
                    event=event,
                    question=question_data['question'],
                    field_type='text'
                )

            # Обрабатываем вопросы с вариантами ответов
            choice_questions = {}
            for key, value in self.request.POST.items():
                if key.startswith('choice_questions'):
                    parts = key.split('[')
                    index = int(parts[1].split(']')[0])
                    field = parts[2].split(']')[0]
                    if index not in choice_questions:
                        choice_questions[index] = {'answers': []}
                    if field == 'question':
                        choice_questions[index][field] = value
                    elif field == 'answers':
                        answer_index = int(parts[3].split(']')[0])
                        while len(choice_questions[index]['answers']) <= answer_index:
                            choice_questions[index]['answers'].append(None)
                        choice_questions[index]['answers'][answer_index] = value

            for question_data in choice_questions.values():
                extra_info = ExtraInfo.objects.create(
                    event=event,
                    question=question_data['question'],
                    field_type='choice'
                )
                for answer in question_data['answers']:
                    if answer:  # Проверяем, что ответ не пустой
                        Choice.objects.create(
                            extra_info=extra_info,
                            value=answer
                        )

            # Обрабатываем настройки команд
            team_questions = {}
            for key, value in self.request.POST.items():
                if key.startswith('team_questions'):
                    parts = key.split('[')
                    index = int(parts[1].split(']')[0])
                    field = parts[2].split(']')[0]
                    if index not in team_questions:
                        team_questions[index] = {}
                    team_questions[index][field] = value

            for question_data in team_questions.values():
                ExtraInfo.objects.create(
                    event=event,
                    field_type='team',
                    min_team_size=int(question_data['min_size']),
                    max_team_size=int(question_data['max_size'])
                )

            return response
        except Exception as e:
            messages.error(self.request, f'Произошла ошибка: {e}')
            return self.form_invalid(form)  # Возвращаем форму с ошибками

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


def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    is_organizer = request.user.is_authenticated and request.user in event.organizers.all()
    # Проверяем, зарегистрирован ли пользователь напрямую или как член команды
    is_registered = event.users_members.filter(id=request.user.id).exists() or \
                    UserAnswer.objects.filter(
                        extra_info__event=event,
                        team_members=request.user
                    ).exists()
    registered_count = event.users_members.count()
    extra_infos = event.extra_info.all()
    
    # Получаем список доступных пользователей для команды
    available_users = User.objects.exclude(id=request.user.id) if request.user.is_authenticated else User.objects.none()

    # Инициализируем форму для дополнительных вопросов
    form = UserAnswerForm(extra_infos=extra_infos, user=request.user) if extra_infos.exists() else None

    # Debug print
    print(f'Debug: Found {extra_infos.count()} questions')
    for info in extra_infos:
        print(f'Question: {info.question} (Type: {info.field_type})')

    # Если есть дополнительные вопросы и пользователь не зарегистрирован, создаем форму
    form = None
    if extra_infos.exists() and not is_registered and request.user.is_authenticated:
        form = UserAnswerForm(extra_infos=extra_infos, user=request.user)

    # Получаем ответы участников
    participants_answers = {}
    for member in event.users_members.all():
        answers = UserAnswer.objects.filter(user=member, extra_info__event=event)
        member_answers = []
        for answer in answers:
            answer_data = {
                'question': answer.extra_info.question,
                'field_type': answer.extra_info.field_type,
            }
            if answer.extra_info.field_type == 'text':
                answer_data['answer'] = answer.answer
            elif answer.extra_info.field_type == 'choice':
                answer_data['answer'] = ', '.join([choice.value for choice in answer.choices.all()])
            elif answer.extra_info.field_type == 'team':
                answer_data['is_captain'] = answer.is_team_captain
                answer_data['team_members'] = [member.Name_User for member in answer.team_members.all()]
            member_answers.append(answer_data)
        participants_answers[member.id] = member_answers

    context = {
        'event': event,
        'is_organizer': is_organizer,
        'is_registered': is_registered,
        'registration_closed': event.registration_closed,
        'registered_count': registered_count,
        'extra_infos': extra_infos,
        'form': form,
        'available_users': available_users,
        'participants_answers': participants_answers,
    }
    
    # Debug print context
    print('Context:', context)
    return render(request, 'events/event_detail_view.html', context)


@login_required
def event_register(request, pk):
    print('Event register view called')
    print('Request method:', request.method)
    print('POST data:', request.POST)
    
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        # Проверяем, что запрос является AJAX
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Invalid request'}, status=400)
            
        if event.registration_closed:
            return JsonResponse({'error': 'Регистрация закрыта'}, status=400)

        if event.max_members > 0 and event.get_registered_count() >= event.max_members:
            return JsonResponse({'error': 'Достигнут лимит участников'}, status=400)

        extra_infos = event.extra_info.all()
        print('Extra infos:', extra_infos)
        
        if extra_infos.exists():
            form = UserAnswerForm(request.POST, extra_infos=extra_infos, user=request.user)
            print('Form is bound:', form.is_bound)
            print('Form data:', form.data)
            
            if form.is_valid():
                print('Form is valid')
                try:
                    # Начинаем транзакцию
                    with transaction.atomic():
                        for extra_info in extra_infos:
                            if extra_info.field_type == 'team':
                                team_members = form.cleaned_data.get(f'team_members_{extra_info.id}', [])
                                print('Team members:', team_members)
                                if not team_members:
                                    # Если участники не выбраны, пропускаем создание команды
                                    continue
                                
                                team_name = form.cleaned_data.get(f'team_name_{extra_info.id}')
                                if team_members:  # Проверяем размер команды только если есть участники
                                    if len(team_members) + 1 < extra_info.min_team_size:
                                        return JsonResponse({
                                            'error': f'В команде должно быть не менее {extra_info.min_team_size} участников (включая капитана)'
                                        }, status=400)
                                    
                                    if len(team_members) + 1 > extra_info.max_team_size:
                                        return JsonResponse({
                                            'error': f'В команде должно быть не более {extra_info.max_team_size} участников (включая капитана)'
                                        }, status=400)
                                    
                                    # Создаем ответ для команды
                                    user_answer = UserAnswer.objects.create(
                                        user=request.user,
                                        extra_info=extra_info,
                                        is_captain=True,
                                        team_name=team_name
                                    )
                                    user_answer.team_members.set(team_members)
                                    print('Team answer created')
                                    
                                    # Регистрируем всех участников команды
                                    for member in team_members:
                                        event.users_members.add(member)
                                        # Создаем ответы для остальных вопросов
                                        for other_info in extra_infos:
                                            if other_info.id != extra_info.id:
                                                UserAnswer.objects.create(
                                                    user=member,
                                                    extra_info=other_info
                                                )
                            else:
                                answer = form.cleaned_data.get(f'extra_{extra_info.id}')
                                if answer:
                                    UserAnswer.objects.create(
                                        user=request.user,
                                        extra_info=extra_info,
                                        answer=answer if isinstance(answer, str) else str(answer.id) if hasattr(answer, 'id') else str(answer)
                                    )
                                    print('Answer created for:', extra_info.question)
                        
                        event.users_members.add(request.user)
                        print('User added to event members')
                        
                        return JsonResponse({
                            'success': True,
                            'message': 'Вы успешно зарегистрировались на мероприятие'
                        })
                except Exception as e:
                    print('Error during registration:', str(e))
                    return JsonResponse({
                        'error': 'Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.'
                    }, status=500)
            else:
                print('Form is invalid')
                print('Form errors:', form.errors)
                return JsonResponse({'errors': form.errors}, status=400)
        else:
            # Если нет дополнительных вопросов, просто регистрируем пользователя
            try:
                event.users_members.add(request.user)
                return JsonResponse({
                    'success': True,
                    'message': 'Вы успешно зарегистрировались на мероприятие'
                })
            except Exception as e:
                print('Error during registration:', str(e))
                return JsonResponse({
                    'error': 'Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.'
                }, status=500)

    return redirect('add_events:event_detail_view', pk=pk)


def add_extra_info(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if not event.is_user_organizer(request.user):
        return HttpResponseForbidden('Только организаторы могут добавлять вопросы')

    if request.method == 'POST':
        form = ExtraInfoForm(request.POST)
        if form.is_valid():
            extra_info = form.save(commit=False)
            extra_info.event = event
            
            # Если это командный вопрос, проверяем размеры команды
            if form.cleaned_data['field_type'] == 'team':
                if not form.cleaned_data.get('min_team_size'):
                    form.add_error('min_team_size', 'Укажите минимальный размер команды')
                    return render(request, 'events/add_extra_info.html', {
                        'event': event,
                        'form': form,
                        'title': 'Добавить дополнительный вопрос'
                    })
                if not form.cleaned_data.get('max_team_size'):
                    form.add_error('max_team_size', 'Укажите максимальный размер команды')
                    return render(request, 'events/add_extra_info.html', {
                        'event': event,
                        'form': form,
                        'title': 'Добавить дополнительный вопрос'
                    })

            extra_info.save()

            # Если это вопрос с вариантами ответа, перенаправляем на страницу добавления вариантов
            if extra_info.field_type == 'choice':
                return redirect('add_events:add_choice', extra_info_id=extra_info.id)
            return redirect('add_events:event_detail_view', pk=event_id)
    else:
        form = ExtraInfoForm()
    
    return render(request, 'events/add_extra_info.html', {
        'event': event,
        'form': form,
        'title': 'Добавить дополнительный вопрос'
    })


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
def search_users(request):
    """Поиск пользователей по ФИО, логину или группе"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'users': []})

    # Исключаем текущего пользователя из результатов
    users = User.objects.exclude(id=request.user.id).filter(
        Q(Name_User__icontains=query) |  # Поиск по ФИО
        Q(username__icontains=query) |   # Поиск по логину
        Q(Number_of_group__icontains=query)  # Поиск по номеру группы
    ).values('id', 'Name_User', 'username', 'Number_of_group')

    # Преобразуем результаты в нужный формат
    users_list = [{
        'id': user['id'],
        'Name_User': user['Name_User'],
        'username': user['username'],
        'Number_of_group': user['Number_of_group']
    } for user in users[:10]]

    # Отладочный вывод
    print(f'Search query: {query}')
    print(f'Found users: {users_list}')

    return JsonResponse({'users': users_list})

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


def add_choice(request, extra_info_id):
    extra_info = get_object_or_404(ExtraInfo, id=extra_info_id)
    if request.method == 'POST':
        form = ChoiceForm(request.POST)
        if form.is_valid():
            choice = form.save(commit=False)
            choice.extra_info = extra_info
            choice.save()
            return redirect('event_detail', event_id=extra_info.event.id)
    else:
        form = ChoiceForm()
    return render(request, 'add_choice.html', {'form': form, 'extra_info': extra_info})

def delete_extra_info(request, extra_info_id):
    extra_info = get_object_or_404(ExtraInfo, id=extra_info_id)
    event_id = extra_info.event.id
    extra_info.delete()
    return redirect('event_detail', event_id=event_id)

def delete_choice(request, choice_id):
    choice = get_object_or_404(Choice, id=choice_id)
    event_id = choice.extra_info.event.id
    choice.delete()
    return redirect('event_detail', event_id=event_id)