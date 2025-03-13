from django import  forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model=Event
        fields=['Event_photo','title_event','description_Event','event_place','event_date','event_time','max_members']




