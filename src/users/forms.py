from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordResetForm, PasswordChangeForm, SetPasswordForm
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


class CustomPasswordResetForm(PasswordResetForm):
    """Password reset form that shows an error if email does not exist in DB and styles the input like login form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        email = self.fields.get("email")
        if email:
            email.widget.attrs.update({
                "class": "form-control",
                "placeholder": "Email",
                "aria-label": "Email",
            })

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Case-insensitive match against our CustomUser model
        if not CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Provided email does not exist.")
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """Password change form styled like the login form inputs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_settings = {
            "old_password": ("Current password", "Password"),
            "new_password1": ("New password", "Password"),
            "new_password2": ("Confirm new password", "Password"),
        }
        for name, (placeholder, aria_label) in field_settings.items():
            field = self.fields.get(name)
            if field:
                field.widget.attrs.update({
                    "class": "form-control",
                    "placeholder": placeholder,
                    "aria-label": aria_label,
                })


class CustomSetPasswordForm(SetPasswordForm):
    """Set-password form (reset confirm) styled like the login form inputs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_settings = {
            "new_password1": ("New password", "Password"),
            "new_password2": ("Confirm new password", "Password"),
        }
        for name, (placeholder, aria_label) in field_settings.items():
            field = self.fields.get(name)
            if field:
                field.widget.attrs.update({
                    "class": "form-control",
                    "placeholder": placeholder,
                    "aria-label": aria_label,
                })
