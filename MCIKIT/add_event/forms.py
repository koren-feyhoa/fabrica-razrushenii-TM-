from django import forms
from django.forms import inlineformset_factory

from .models import Event, Question, AnswerOption
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_date, parse_time

User = get_user_model()

class EventForm(forms.ModelForm):
    event_date = forms.DateField(
        required=True,
        help_text="Дата проведения мероприятия",
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'type': 'date',
                'class': 'form-control',
            }
        )
    )
    event_time = forms.TimeField(
        required=True,
        help_text="Время начала мероприятия",
        widget=forms.TimeInput(
            format='%H:%M',
            attrs={
                'type': 'time',
                'class': 'form-control',
            }
        )
    )
    additional_organizers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role__in=['pro_user', 'super_user']),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        help_text="Выберите дополнительных организаторов из списка ProUser"
    )

    class Meta:
        model = Event
        fields = [
            'title_event',
            'description_Event',
            'event_place',
            'event_date',
            'event_time',
            'Event_photo',
            'max_members',
            'additional_organizers'
        ]
        widgets = {
            'title_event': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description_Event': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': True}),
            'event_place': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'Event_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'max_members': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
QuestionFormSet = inlineformset_factory(Event, Question, fields=('text',), extra=1, can_delete=True)
AnswerOptionFormSet = inlineformset_factory(Question, AnswerOption, fields=('text',), extra=2, can_delete=True)


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

class AnswerOptionForm(forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ['text']


