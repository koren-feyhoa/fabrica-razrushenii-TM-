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
from .models import Event, ExtraInfo, Choice, UserAnswer, EventRating
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
    
    def test_func(self):
        event = self.get_object()
        return event.is_user_organizer(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        
        # Получаем все команды для этого мероприятия
        teams = {}
        for answer in UserAnswer.objects.filter(
            extra_info__event=event,
            extra_info__field_type='team',
            is_team_captain=True
        ).select_related('user', 'extra_info'):
            teams[answer.team_name] = {
                'captain': answer.user,
                'members': list(answer.team_members.all()),
                'answers': []
            }
            
            # Добавляем ответы капитана
            captain_answers = UserAnswer.objects.filter(
                user=answer.user,
                extra_info__event=event
            ).exclude(extra_info__field_type='team')
            
            for ans in captain_answers:
                teams[answer.team_name]['answers'].append({
                    'question': ans.extra_info.title or ans.extra_info.question,
                    'answer': ans.answer
                })
        
        # Получаем индивидуальных участников (не в командах)
        individual_participants = event.users_members.exclude(
            id__in=UserAnswer.objects.filter(
                extra_info__event=event,
                extra_info__field_type='team'
            ).values_list('user_id', flat=True)
        )
        
        context.update({
            'teams': teams,
            'individual_participants': individual_participants,
        })
        return context


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
    team_answer = UserAnswer.objects.filter(
        extra_info__event=event,
        team_members=request.user,
        extra_info__field_type='team'
    ).first()
    
    is_registered = event.users_members.filter(id=request.user.id).exists() or team_answer is not None
    team_name = team_answer.team_name if team_answer else None
    registered_count = event.users_members.count()
    extra_infos = event.extra_info.all()
    
    # Получаем список доступных пользователей для команды
    available_users = User.objects.exclude(id=request.user.id) if request.user.is_authenticated else User.objects.none()

    # Если есть дополнительные вопросы и пользователь не зарегистрирован, создаем форму
    form = None
    if extra_infos.exists() and not is_registered and request.user.is_authenticated:
        form = UserAnswerForm(extra_infos=extra_infos, user=request.user)

    # Получаем ответы участников
    participants_answers = {}
    
    # Получаем все ответы на вопросы (включая командные и индивидуальные)
    all_answers = UserAnswer.objects.filter(
        extra_info__event=event
    ).select_related('user', 'extra_info').prefetch_related('team_members')
    
    # Группируем ответы по пользователям
    for answer in all_answers:
        if answer.user.id not in participants_answers:
            participants_answers[answer.user.id] = []
        
        answer_data = {
            'field_type': answer.extra_info.field_type,
            'question': answer.extra_info.question,
            'answer': answer.answer,
        }
        
        if answer.extra_info.field_type == 'team':
            answer_data.update({
                'is_team_captain': answer.is_team_captain,
                'team_name': answer.team_name,
                'team_members': list(answer.team_members.all())
            })
        
        participants_answers[answer.user.id].append(answer_data)

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
        'team_name': team_name
    }
    
    return render(request, 'events/event_detail_view.html', context)


@login_required
def event_register(request, pk):
    print('Event register view called')
    print('Request method:', request.method)
    print('POST data:', request.POST)
    
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        if event.registration_closed:
            messages.error(request, 'Регистрация закрыта')
            return redirect('add_events:event_detail_view', pk=pk)

        if event.max_members > 0 and event.get_registered_count() >= event.max_members:
            messages.error(request, 'Достигнут лимит участников')
            return redirect('add_events:event_detail_view', pk=pk)

        extra_infos = event.extra_info.all()
        print('Extra infos:', extra_infos)
        
        # Проверяем, есть ли дополнительные вопросы
        if extra_infos.exists():
            # Если запрос не AJAX при наличии доп. вопросов
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                messages.error(request, 'Пожалуйста, заполните все необходимые поля')
                return redirect('add_events:event_detail_view', pk=pk)
                
            form = UserAnswerForm(request.POST, extra_infos=extra_infos, user=request.user)
            print('Form is bound:', form.is_bound)
            print('Form data:', form.data)
            
            if form.is_valid():
                print('Form is valid')
                try:
                    # Начинаем транзакцию
                    with transaction.atomic():
                        # Регистрируем текущего пользователя
                        event.users_members.add(request.user)
                        
                        for extra_info in extra_infos:
                            if extra_info.field_type == 'team':
                                team_name = form.cleaned_data.get(f'team_name_{extra_info.id}')
                                team_members = form.cleaned_data.get(f'team_members_{extra_info.id}', [])
                                print(f'Team name: {team_name}')
                                print(f'Team members: {team_members}')
                                
                                if team_members:  # Проверяем размер команды только если есть участники
                                    if len(team_members) + 1 < extra_info.min_team_size:
                                        return JsonResponse({
                                            'error': f'В команде должно быть не менее {extra_info.min_team_size} участников (включая капитана)'
                                        }, status=400)
                                    
                                    if len(team_members) + 1 > extra_info.max_team_size:
                                        return JsonResponse({
                                            'error': f'В команде должно быть не более {extra_info.max_team_size} участников (включая капитана)'
                                        }, status=400)
                                    
                                    # Создаем ответ для капитана команды
                                    captain_answer = UserAnswer.objects.create(
                                        user=request.user,
                                        extra_info=extra_info,
                                        is_team_captain=True,
                                        team_name=team_name
                                    )
                                    # Добавляем капитана в список участников команды
                                    all_team_members = [request.user] + list(team_members)
                                    captain_answer.team_members.set(all_team_members)
                                    print('Captain answer created')
                                    
                                    # Регистрируем участников команды
                                    for member in team_members:
                                        event.users_members.add(member)
                                        # Создаем ответ для участника команды
                                        member_answer = UserAnswer.objects.create(
                                            user=member,
                                            extra_info=extra_info,
                                            is_team_captain=False,
                                            team_name=team_name
                                        )
                                        member_answer.team_members.set(all_team_members)
                                        print(f'Member answer created for {member}')
                            else:
                                answer = form.cleaned_data.get(f'extra_{extra_info.id}')
                                if answer:
                                    UserAnswer.objects.create(
                                        user=request.user,
                                        extra_info=extra_info,
                                        answer=answer if isinstance(answer, str) else str(answer.id) if hasattr(answer, 'id') else str(answer)
                                    )
                                    print('Answer created for:', extra_info.question)
                        
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
                messages.success(request, 'Вы успешно зарегистрировались на мероприятие')
                return redirect('add_events:event_detail_view', pk=pk)
            except Exception as e:
                print('Error during registration:', str(e))
                messages.error(request, 'Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.')
                return redirect('add_events:event_detail_view', pk=pk)

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
            return redirect('main')
        return HttpResponseForbidden('У вас нет прав для удаления этого мероприятия')
    return HttpResponseForbidden()


def get_pro_users(request):
    """Возвращает список ProUser в формате JSON"""
    pro_users = User.objects.filter(role__in=['pro_user', 'super_user']).values('id', 'Name_User')
    return JsonResponse(list(pro_users), safe=False)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
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


@login_required
def add_review(request, pk):
    event = get_object_or_404(Event, pk=pk)

    # Проверяем, не оставлял ли уже пользователь отзыв
    existing_review = EventRating.objects.filter(user=request.user, event=event).first()

    if request.method == 'POST':
        if existing_review:
            messages.error(request, 'Вы уже оставляли отзыв на это мероприятие')
            return redirect(reverse('add_events:event_reviews', kwargs={'pk': pk}))

        rating = request.POST.get('rating')
        likes = request.POST.get('likes', '').strip()
        dislikes = request.POST.get('dislikes', '').strip()

        # Валидация данных
        if not rating:
            messages.error(request, 'Пожалуйста, укажите оценку')
            return redirect(reverse('add_events:add_review', kwargs={'pk': pk}))

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            messages.error(request, 'Оценка должна быть числом от 1 до 5')
            return redirect(reverse('add_events:add_review', kwargs={'pk': pk}))

        # Создаем или обновляем отзыв
        try:
            if existing_review:
                # Обновляем существующий отзыв
                existing_review.rating = rating
                existing_review.likes = likes if likes else None
                existing_review.dislikes = dislikes if dislikes else None
                existing_review.save()
                messages.success(request, 'Ваш отзыв успешно обновлен!')
            else:
                # Создаем новый отзыв
                EventRating.objects.create(
                    user=request.user,
                    event=event,
                    rating=rating,
                    likes=likes if likes else None,
                    dislikes=dislikes if dislikes else None
                )
                messages.success(request, 'Ваш отзыв успешно сохранен!')

            return redirect(reverse('add_events:event_reviews', kwargs={'pk': pk}))
        except Exception as e:
            messages.error(request, f'Произошла ошибка при сохранении отзыва: {e}')
            return redirect(reverse('add_events:add_review', kwargs={'pk': pk}))

    # Для GET запроса показываем форму
    context = {
        'event': event,
        'existing_review': existing_review,
        'user_review_exists': existing_review is not None
    }
    return render(request, 'events/add_review.html', context)


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(EventRating, id=review_id)
    event = review.event

    # Проверяем права: либо автор отзыва, либо организатор мероприятия
    if request.user != review.user and not event.is_user_organizer(request.user):
        messages.error(request, 'У вас нет прав для удаления этого отзыва')
        return redirect('add_events:event_reviews', pk=event.id)

    review.delete()
    messages.success(request, 'Отзыв успешно удален')
    return redirect('add_events:event_reviews', pk=event.id)


class EventReviewsView(DetailView):
    model = Event
    template_name = 'events/event_reviews.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        reviews = event.ratings.select_related('user').order_by('-timestamp')

        # Проверяем, может ли текущий пользователь оставить отзыв
        user_can_review = False
        if self.request.user.is_authenticated:
            user_can_review = (
                    event.users_members.filter(id=self.request.user.id).exists() and
                    not reviews.filter(user=self.request.user).exists()
            )

        context.update({
            'reviews': reviews,
            'can_review': user_can_review,
            'user_review_exists': reviews.filter(
                user=self.request.user).exists() if self.request.user.is_authenticated else False
        })
        return context


def user_profile(request):
    if not request.user.is_authenticated:
        return redirect('users:login')

    now = timezone.now()
    attended_events = []

    # Получаем все мероприятия пользователя
    user_events = Event.objects.filter(users_members=request.user).order_by('-event_date')

    for event in user_events:
        # Проверяем, прошло ли мероприятие
        event_datetime = datetime.combine(event.event_date, event.event_time)
        has_started = event_datetime <= now

        # Получаем отзыв пользователя
        rating = EventRating.objects.filter(event=event, user=request.user).first()

        attended_events.append({
            'event': event,
            'has_started': has_started,
            'rating': rating
        })

    # Получаем организованные мероприятия (если пользователь организатор)
    organized_events = []
    if request.user.is_pro_user or request.user.is_super_user:
        organized_events = Event.objects.filter(organizers=request.user).order_by('-event_date')

    context = {
        'user': request.user,
        'attended_events': attended_events,
        'organized_events': organized_events,
        'now': now
    }

    return render(request, 'users/user_profile.html', context)