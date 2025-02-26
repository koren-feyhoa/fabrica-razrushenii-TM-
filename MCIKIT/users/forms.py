from django import  forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User
from django.forms import ModelForm, TextInput


class LoginUserForm(AuthenticationForm):
    username=forms.CharField(label="Логин",
        widget=forms.TextInput(attrs={'class':'form-input'}))
    password = forms.CharField(label="Пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    class Meta:
        model=get_user_model()
        fields=['username', 'password']

class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label="Логин")
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput())
    password2 = None
    first_name=None
    last_name=None
    class Meta:
        model=get_user_model()
        fields=['Name_User','Number_of_group','VK_id','email', 'username', 'password1']
        labels= {
            'Name_User': 'ФИО',
            'email': 'E-mail',
            }
        widgets={
            'email': forms.TextInput(attrs={'class': 'form-input'})
        }
    def clean_email(self):
        email=self.cleaned_data['email']
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("Такой E-mail уже существует!")
        return email

class UserSettingsForm(forms.ModelForm):
    Name_User = forms.CharField(max_length=30, label='ФИО')
    VK_id = forms.CharField(max_length=100, label='ВК ID')
    Number_of_group = forms.CharField(max_length=100, label='Номер группы')
    email = forms.EmailField(label='Email')
    username = forms.CharField(max_length=150, label='Логин', disabled=True)  # Делаем поле недоступным для изменения
    Avatar = forms.ImageField(required=False, label='Аватарка')

    class Meta:
        model = User
        fields = ['Name_User', 'VK_id', 'Number_of_group', 'email', 'username', 'Avatar']
