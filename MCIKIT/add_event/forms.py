from django import forms
from .models import Event
from django.contrib.auth import get_user_model

User = get_user_model()

class EventForm(forms.ModelForm):
    event_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Дата проведения мероприятия"
    )
    event_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        help_text="Время начала мероприятия"
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
            'title_event': forms.TextInput(attrs={'class': 'form-control'}),
            'description_Event': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'event_place': forms.TextInput(attrs={'class': 'form-control'}),
            'Event_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'max_members': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }




