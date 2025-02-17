from django.urls import path
from . import views


urlpatterns=[
    path('sigh_in',views.sigh_in, name='sigh_in'),
    path('log_in',views.log_in, name='log_in'),
]