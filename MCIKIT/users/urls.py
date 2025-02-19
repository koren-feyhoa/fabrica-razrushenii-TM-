from django.contrib.auth.views import LogoutView
from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework.urls import app_name

from . import views
app_name="users"

urlpatterns=[

    path('login/',views.LoginUser.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]