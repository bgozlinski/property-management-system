from django import forms
from .models import TenantInvitation, Reminder


"""
This module provides forms for notifications and invitations in the system.

It includes forms for creating and updating tenant invitations and reminders.
"""


class TenantInvitationForm(forms.ModelForm):
    """
    Form for creating and updating tenant invitations.

    This form allows landlords to invite tenants to join the system by
    providing their email address and selecting a property.
    """

    class Meta:
        """
        Metadata for the TenantInvitationForm.

        Specifies the model, fields to include, labels, and help texts.
        """

        model = TenantInvitation
        fields = ["email", "property_unit"]
        labels = {
            "email": "Tenant email address",
            "property_unit": "Property",
        }
        help_texts = {
            "email": "Enter the email address of the future tenant",
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom filtering for properties.

        Filters the property_unit queryset to only show properties owned
        by the specified landlord.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments, including 'landlord'.
        """
        landlord = kwargs.pop("landlord", None)
        super().__init__(*args, **kwargs)

        if landlord:
            self.fields["property_unit"].queryset = self.fields[
                "property_unit"
            ].queryset.filter(landlord__user=landlord)


class ReminderForm(forms.ModelForm):
    """
    Form for creating and updating reminders.

    This form allows users to create and update reminders with a title,
    description, due date, and associated property.
    """

    class Meta:
        """
        Metadata for the ReminderForm.

        Specifies the model, fields to include, and widget styling.
        """

        model = Reminder
        fields = ["title", "description", "due_date", "unit"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "due_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "unit": forms.Select(attrs={"class": "form-control"}),
        }
