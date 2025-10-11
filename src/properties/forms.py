from django import forms
from .models import Property, Building, Unit, Equipment, Meter, MeterReading


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


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ["name", "address", "city", "postal_code"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
        }


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ["building", "number", "floor", "area_m2", "unit_type", "status"]
        widgets = {
            "building": forms.Select(attrs={"class": "form-control"}),
            "number": forms.TextInput(attrs={"class": "form-control"}),
            "floor": forms.NumberInput(attrs={"class": "form-control"}),
            "area_m2": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "unit_type": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ["unit", "name", "description", "serial_number"]
        widgets = {
            "unit": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
        }


class MeterForm(forms.ModelForm):
    class Meta:
        model = Meter
        fields = ["unit", "meter_type", "serial"]
        widgets = {
            "unit": forms.Select(attrs={"class": "form-control"}),
            "meter_type": forms.Select(attrs={"class": "form-control"}),
            "serial": forms.TextInput(attrs={"class": "form-control"}),
        }


class MeterReadingForm(forms.ModelForm):
    class Meta:
        model = MeterReading
        fields = ["meter", "date", "value"]
        widgets = {
            "meter": forms.Select(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "value": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
        }
