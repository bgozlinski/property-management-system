from django import forms
from .models import Property


"""
This module provides forms for property management in the system.

It includes forms for creating and updating property information.
"""


class PropertyForm(forms.ModelForm):
    """
    Form for creating and updating property information.

    This form includes fields for all property attributes and applies
    appropriate styling to form widgets.
    """

    class Meta:
        """
        Metadata for the PropertyForm.

        Specifies the model, fields to include, and widget styling.
        """

        model = Property
        fields = [
            "address",
            "city",
            "postal_code",
            "area_m2",
            "current_rent",
            "additional_costs",
            "status",
        ]
        widgets = {
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "area_m2": forms.NumberInput(attrs={"class": "form-control"}),
            "current_rent": forms.NumberInput(attrs={"class": "form-control"}),
            "additional_costs": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }
