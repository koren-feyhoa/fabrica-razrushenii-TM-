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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['field_type'].widget.attrs.update({'class': 'form-control', 'onchange': 'handleFieldTypeChange(this)'})
        self.fields['question'].widget.attrs.update({'class': 'form-control'})
        self.fields['allow_multiple'].widget.attrs.update({'class': 'form-control'})
        self.fields['min_team_size'].widget.attrs.update({'class': 'form-control', 'min': '1'})
        self.fields['max_team_size'].widget.attrs.update({'class': 'form-control', 'min': '1'})

    class Meta:
        model = ExtraInfo
        fields = ['question', 'field_type', 'allow_multiple', 'min_team_size', 'max_team_size']

    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        min_team_size = cleaned_data.get('min_team_size')
        max_team_size = cleaned_data.get('max_team_size')

        if field_type == 'team':
            if not min_team_size or not max_team_size:
                raise forms.ValidationError('Для команды необходимо указать минимальный и максимальный размер')
            if min_team_size > max_team_size:
                raise forms.ValidationError({
                    'min_team_size': 'Минимальный размер команды не может быть больше максимального'
                })
            if min_team_size < 1:
                raise forms.ValidationError('Минимальный размер команды должен быть не менее 1')
        return cleaned_data

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['value']


class UserAnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        extra_infos = kwargs.pop('extra_infos', [])
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for info in extra_infos:
            if info.field_type == 'team':
                info_id = str(info.id)
                self.fields[f'team_members_{info_id}'] = forms.ModelMultipleChoiceField(
                    label='Участники команды',
                    queryset=User.objects.exclude(id=user.id) if user else User.objects.none(),
                    required=False,
                    widget=forms.SelectMultiple(attrs={'class': 'form-control', 'style': 'display: none;'}),
                    help_text=f'Минимум {info.min_team_size-1}, максимум {info.max_team_size-1} участников (вы будете капитаном команды)'
                )
            elif info.question:
                if info.field_type == 'text':
                    self.fields[f'extra_{info.id}'] = forms.CharField(
                        label=info.question,
                        required=True,
                        widget=forms.Textarea(attrs={'class': 'form-control'})
                    )
                elif info.field_type == 'choice':
                    choices = Choice.objects.filter(extra_info=info)
                    if info.allow_multiple:
                        self.fields[f'extra_{info.id}'] = forms.ModelMultipleChoiceField(
                            label=info.question,
                            queryset=choices,
                            required=True,
                            widget=forms.CheckboxSelectMultiple
                        )
                    else:
                        self.fields[f'extra_{info.id}'] = forms.ModelChoiceField(
                            label=info.question,
                            queryset=choices,
                            required=True,
                            widget=forms.RadioSelect
                        )

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            if field_name.startswith('team_members_'):
                info_id = field_name.split('_')[-1]
                team_members = value
                extra_info = ExtraInfo.objects.get(id=info_id)

                if not team_members:
                    return cleaned_data  # Если нет участников, пропускаем валидацию
                if len(team_members) + 1 < extra_info.min_team_size:
                    raise forms.ValidationError(
                        f'В команде должно быть не менее {extra_info.min_team_size} участников (включая капитана)'
                    )
                if len(team_members) + 1 > extra_info.max_team_size:
                    raise forms.ValidationError(
                        f'В команде должно быть не более {extra_info.max_team_size} участников (включая капитана)'
                    )

        return cleaned_data

