from django import forms

from .models import Payment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        # Hide computed fields and 'water' from the form while keeping them in the model
        exclude = ("total_amount", "water", "tax_rate", "tax_amount")
        widgets = {
            "date_due": forms.DateInput(attrs={"type": "date"}),
            "date_paid": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        # Ensure numeric fields default to 0 when missing (excluding 'water')
        for f in ["base_rent", "coop_fee", "electricity", "gas", "other_fees"]:
            cleaned[f] = float(cleaned.get(f) or 0.0)
        return cleaned
