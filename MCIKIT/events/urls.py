from django.urls import path
from . import views


urlpatterns=[
    path('upcoming',views.upcoming, name='upcoming'),
    path('made',views.made, name='made'),


]