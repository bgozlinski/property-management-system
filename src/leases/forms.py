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
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        for name in ["unit", "tenant"]:
            if name in self.fields:
                self.fields[name].widget.attrs.setdefault("class", "form-select")

        # Restrict unit choices to AVAILABLE units; include instance's current unit on edit
        if "unit" in self.fields:
            from django.db.models import Q
            from properties.models import Unit  # local import to avoid cycles at import time

            unit_qs = None
            instance_unit_id = getattr(getattr(self, "instance", None), "unit_id", None)

            if self.request and getattr(self.request, "user", None):
                user = self.request.user
                try:
                    if hasattr(user, "role") and int(user.role) == 2:
                        # Landlord: scope units to landlord's buildings
                        base_qs = Unit.objects.filter(building__landlord__user=user)
                    else:
                        # Other roles: all units
                        base_qs = Unit.objects.all()
                except Exception:
                    base_qs = Unit.objects.all()
            else:
                base_qs = Unit.objects.all()

            # Only free units for new agreements: exclude units with an active agreement.
            # Active = (start <= today or start is null) AND (no end or end >= today)
            from django.utils import timezone
            today = timezone.localdate() if hasattr(timezone, "localdate") else timezone.now().date()

            active_unit_ids = (
                RentalAgreement.objects.filter(unit__isnull=False)
                .filter(
                    (Q(start_date__isnull=True) | Q(start_date__lte=today))
                    & (Q(end_date__isnull=True) | Q(end_date__gte=today))
                )
                .values_list("unit_id", flat=True)
            )

            if instance_unit_id:
                unit_qs = base_qs.filter(Q(pk=instance_unit_id) | ~Q(pk__in=active_unit_ids))
            else:
                unit_qs = base_qs.exclude(pk__in=active_unit_ids)

            self.fields["unit"].queryset = unit_qs
            self.fields["unit"].empty_label = "Select a unit (optional)"

        if "unit" in self.fields and not getattr(self.fields["unit"], "queryset", None).exists():
            self.fields["unit"].empty_label = "No units available — optional"
