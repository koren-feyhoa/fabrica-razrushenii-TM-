from django.urls import path
from . import views
from .views import (
    EventListView,
    EventCreateView,
    EventUpdateView,
    EventReviewsView,
    EventParticipantsView,
    event_register,
    event_unregister,
    event_delete,
    add_event,
    get_pro_users,
    event_detail_view,
    search_users
)

app_name = 'add_events'

urlpatterns = [
    path('', EventListView.as_view(), name='event_list'),
    path('add/', add_event, name='add_event'),
    path('create/', EventCreateView.as_view(), name='event_create'),
    path('<int:pk>/', event_detail_view, name='event_detail_view'),
    path('search_users/', search_users, name='search_users'),
    path('<int:pk>/update/', EventUpdateView.as_view(), name='event_update'),
    path('<int:pk>/participants/', EventParticipantsView.as_view(), name='event_participants'),
    path('<int:pk>/register/', event_register, name='event_register'),
    path('<int:pk>/unregister/', event_unregister, name='event_unregister'),
    path('<int:pk>/delete/', event_delete, name='event_delete'),
    path('<int:pk>/toggle-registration/', views.toggle_registration, name='toggle_registration'),
    path('get-pro-users/', get_pro_users, name='get_pro_users'),
    path('<int:pk>/reviews/', EventReviewsView.as_view(), name='event_reviews'),
]