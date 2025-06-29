from django import forms
from .models import TenantInvitation


class TenantInvitationForm(forms.ModelForm):
    class Meta:
        model = TenantInvitation
        fields = ['email', 'property_unit']
        labels = {
            'email': 'Tenant email address',
            'property_unit': 'Property',
        }
        help_texts = {
            'email': 'Enter the email address of the future tenant',
        }

    def __init__(self, *args, **kwargs):
        landlord = kwargs.pop('landlord', None)
        super().__init__(*args, **kwargs)

        if landlord:
            # Filter properties to only those owned by a specific landlord
            self.fields['property_unit'].queryset = self.fields['property_unit'].queryset.filter(landlord__user=landlord)