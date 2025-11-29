from .models import User, Comment
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label='',  # вимикаємо label
        widget=forms.TextInput(attrs={'placeholder': "Ім'я користувача"})
    )
    email = forms.EmailField(
        label='',
        widget=forms.EmailInput(attrs={'placeholder': 'Електронна пошта'})
    )
    password1 = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'})
    )
    password2 = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Підтвердіть пароль'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='',
        widget=forms.TextInput(attrs={'placeholder': "Ім'я користувача"})
    )
    password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'})
    )

class QuestionForm(forms.Form):
    question = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={'placeholder': 'Ваше питання', 'rows': 4})
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Напишіть коментар...'
            })
        }
        labels = {
            'text': ''
        }