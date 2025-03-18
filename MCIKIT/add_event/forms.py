from django import forms
from django.forms import inlineformset_factory

from .models import Event, ExtraInfo, Choice
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
            'additional_organizers',
        ]
        widgets = {
            'title_event': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description_Event': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': True}),
            'event_place': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'Event_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'max_members': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class ExtraInfoForm(forms.ModelForm):
    class Meta:
        model = ExtraInfo
        fields = ['question', 'field_type']

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['value']


class UserAnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        extra_infos = kwargs.pop('extra_infos', [])
        super().__init__(*args, **kwargs)
        for info in extra_infos:
            if info.question:
                if info.field_type == 'text':
                    self.fields[f'extra_{info.id}'] = forms.CharField(label=info.question, required=True)
                elif info.field_type == 'choice':
                    choices = Choice.objects.filter(extra_info=info)
                    self.fields[f'extra_{info.id}'] = forms.ChoiceField(label=info.question, choices=[(choice.id, choice.value) for choice in choices], required=True)


