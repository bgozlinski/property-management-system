from django import forms

from .models import RentalAgreement


class RentalAgreementForm(forms.ModelForm):
    class Meta:
        model = RentalAgreement
        fields = [
            "unit",
            "tenant",
            "start_date",
            "end_date",
            "base_rent",
            "coop_fee",
            "electricity",
            "gas",
            "other_fees",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        # Pop request if provided by the view to filter choices
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # Ensure select widgets have consistent styling
        for name in ["unit", "tenant"]:
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault("class", "form-select")

        # If we know the current landlord, try to filter units to those owned by them.
        if self.request and getattr(self.request, "user", None):
            user = self.request.user
            try:
                # Landlord role == 2 (see users.models)
                if hasattr(user, "role") and int(user.role) == 2:
                    if "unit" in self.fields:
                        from properties.models import Unit  # local import to avoid cycles at import time
                        uqs = Unit.objects.filter(building__landlord__user=user)
                        self.fields["unit"].queryset = uqs
                        self.fields["unit"].empty_label = "Select a unit (optional)"
                else:
                    # Admins and others see all units
                    if "unit" in self.fields:
                        from properties.models import Unit
                        self.fields["unit"].queryset = Unit.objects.all()
                        self.fields["unit"].empty_label = "Select a unit (optional)"
            except Exception:
                # Keep default queryset (all units) on any unexpected error.
                if "unit" in self.fields:
                    from properties.models import Unit
                    self.fields["unit"].queryset = Unit.objects.all()
                    self.fields["unit"].empty_label = "Select a unit (optional)"

        # If there are no units, still show a helpful empty label
        if "unit" in self.fields and not getattr(self.fields["unit"], "queryset", None).exists():
            self.fields["unit"].empty_label = "No units available — optional"
