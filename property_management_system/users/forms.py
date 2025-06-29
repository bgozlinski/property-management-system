from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    is_landlord = forms.BooleanField(
        required=False,
        label="I want to register as a Landlord",
        help_text="Check this box if you want to register as a Landlord"
    )

    class Meta:
        model = CustomUser
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ("email",)