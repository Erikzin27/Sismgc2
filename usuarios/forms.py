from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, UserProfile


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "is_staff", "is_superuser")


class UserUpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "role", "is_staff", "is_superuser", "is_active")


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("foto", "tema", "telefone", "setor")


class UserSelfForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
