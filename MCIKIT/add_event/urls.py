from django.urls import path
from . import views
from .views import (
    EventListView,
    EventDetailView,
    EventCreateView,
    EventUpdateView,
    EventParticipantsView,
    event_register,
    event_unregister,
    event_delete,
    add_event,
    get_pro_users
)

urlpatterns = [
    path('', EventListView.as_view(), name='event_list'),
    path('add/', add_event, name='add_event'),
    path('create/', EventCreateView.as_view(), name='event_create'),
    path('<int:pk>/', EventDetailView.as_view(), name='event_detail_view'),
    path('<int:pk>/update/', EventUpdateView.as_view(), name='event_update'),
    path('<int:pk>/participants/', EventParticipantsView.as_view(), name='event_participants'),
    path('<int:pk>/register/', event_register, name='event_register'),
    path('<int:pk>/unregister/', event_unregister, name='event_unregister'),
    path('<int:pk>/delete/', event_delete, name='event_delete'),
    path('get-pro-users/', get_pro_users, name='get_pro_users'),
]