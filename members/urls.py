from django.urls import path
from . import views

urlpatterns = [
    path('api/member/', views.MemberListCreate.as_view() ),
]