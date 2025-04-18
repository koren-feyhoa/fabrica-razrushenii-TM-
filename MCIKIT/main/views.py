from django.shortcuts import render
import json
from add_event.models import Event
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder

def main(request):
    # Получаем все мероприятия
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
    
    return render(request, 'main_page.html', {
        'events_json': events_json
    })
