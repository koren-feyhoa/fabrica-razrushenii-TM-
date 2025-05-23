# from tkinter.font import names

from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, reverse_lazy
from django.urls import path
from . import views
from .views import RegisterUser, profile, UserSettingsView, rate_event, personal

app_name="users"

urlpatterns=[

    path('login/',views.LoginUser.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('register/personal/', personal, name='personal'),
    path('password-reset/',
         PasswordResetView.as_view(
             template_name="users/password_reset_form.html",
             email_template_name="users/password_reset_email.html",
             success_url=reverse_lazy("users:password_reset_done")),
         name='password_reset'),
    path('password-reset/done/',
         PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(
             template_name="users/password_reset_confirm.html",
             success_url=reverse_lazy("users:password_reset_complete")), name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"), name='password_reset_complete'),
    path('accounts/profile/', profile, name='user_profile'),
    path('accounts/settings/', UserSettingsView, name='user_settings'),
path('users/', views.user_list, name='user_list'),
    path('make-pro-user/<int:user_id>/', views.make_pro_user, name='make_pro_user'),
    path('make-regular-user/<int:user_id>/', views.make_regular_user, name='make_regular_user'),

 path('rate_event/<int:event_id>/', rate_event, name='rate_event'),


]