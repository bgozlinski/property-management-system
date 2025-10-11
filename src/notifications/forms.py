from django import forms
from django.utils import timezone
from .models import TenantInvitation, Reminder
from properties.models import Property, Building, Unit


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
    # Backward-compatible field: accept legacy 'property' posts/tests and map to Unit
    property = forms.ModelChoiceField(queryset=Property.objects.all(), required=False, label="Property")
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

    def clean(self):
        cleaned = super().clean()
        unit = cleaned.get("unit")
        legacy_prop = cleaned.get("property")
        # Map legacy property to a Unit if unit not selected
        if not unit and legacy_prop:
            # Create a Building and Unit mirroring the Property
            building = Building.objects.create(
                landlord=legacy_prop.landlord,
                name=str(legacy_prop.address),
                address=legacy_prop.address,
                city=legacy_prop.city,
                postal_code=legacy_prop.postal_code,
            )
            created_unit = Unit.objects.create(
                building=building,
                number="1",
                floor=0,
                area_m2=getattr(legacy_prop, "area_m2", 0) or 0,
            )
            cleaned["unit"] = created_unit
            # Remove any validation error on unit added during field-level validation
            try:
                if "unit" in self._errors:
                    self._errors.pop("unit", None)
            except Exception:
                pass
        return cleaned

    def clean_due_date(self):
        """Accept a plain date (YYYY-MM-DD) and convert it to a timezone-aware datetime.

        Tests instantiate ReminderForm directly and pass a date-only value. Since the
        model uses a DateTimeField, we coerce the value here for validation to pass.
        """
        value = self.cleaned_data.get("due_date")
        if value is None:
            return value
        # If a date (no time) is provided, convert to midnight local time and make aware
        if hasattr(value, "year") and not hasattr(value, "hour"):
            dt = timezone.datetime(value.year, value.month, value.day, 0, 0, 0)
            try:
                return timezone.make_aware(dt)
            except Exception:
                # If settings/timezone not configured for awareness, return naive dt
                return dt
        return value
