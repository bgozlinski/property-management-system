from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser


"""
This module provides custom forms for user creation and modification.

It includes forms for user registration with role selection and user profile editing.
"""


class CustomUserCreationForm(UserCreationForm):
    """
    Custom form for user registration.

    Extends Django's UserCreationForm to use email as the identifier
    and adds an option for users to register as landlords.
    """

    is_landlord = forms.BooleanField(
        required=False,
        label="I want to register as a Landlord",
        help_text="Check this box if you want to register as a Landlord",
    )

    class Meta:
        """Metadata for the form, specifying the model and fields."""

        model = CustomUser
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    """
    Custom form for modifying existing users.

    Extends Django's UserChangeForm to use the CustomUser model
    and focus on the email field.
    """

    class Meta:
        """Metadata for the form, specifying the model and fields."""

        model = CustomUser
        fields = ("email",)
