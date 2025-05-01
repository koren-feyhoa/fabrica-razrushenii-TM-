from django.shortcuts import render
import json
from add_event.models import Event
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.db.models import Q

def main(request):
    # Получаем актуальные мероприятия (которые еще не закончились)
    today = timezone.now().date()
    current_time = timezone.now().time()
    
    # Фильтруем мероприятия, которые еще не закончились
    upcoming_events = Event.objects.filter(
        Q(event_date__gt=today) |
        Q(event_date=today, event_time__gte=current_time)
    ).order_by('event_date', 'event_time')
    
    # Получаем все мероприятия для календаря
    events = Event.objects.all()
    
    # Создаем словарь, где ключ - дата, значение - список мероприятий на эту дату
    events_by_date = {}
    for event in events:
        date_str = event.event_date.isoformat()
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        
        events_by_date[date_str].append({
            'id': event.id,
            'title': event.title_event,
            'description': event.description_Event,
            'date': event.event_date.strftime('%d.%m.%Y'),
            'time': event.event_time.strftime('%H:%M'),
        })
    
    # Преобразуем словарь в JSON для передачи в шаблон
    events_json = json.dumps(events_by_date, cls=DjangoJSONEncoder)
    
    # Подготавливаем данные для карусели
    carousel_events = [{
        'id': event.id,
        'title': event.title_event,
        'date': event.event_date.strftime('%d.%m.%Y'),
        'time': event.event_time.strftime('%H:%M'),
        'photo': event.Event_photo.url if event.Event_photo else None
    } for event in upcoming_events]

    return render(request, 'main_page.html', {
        'events_json': events_json,
        'carousel_events': carousel_events
    })
