from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, Http404

from .models import RentalAgreement
from .forms import RentalAgreementForm


class RentalAgreementListView(ListView):
    model = RentalAgreement
    template_name = "leases/rentalagreement_list.html"
    context_object_name = "agreements"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .forms import RentalAgreementForm
        ctx["agreement_form"] = RentalAgreementForm(request=self.request)
        return ctx


class RentalAgreementCreateView(CreateView):
    model = RentalAgreement
    form_class = RentalAgreementForm
    template_name = "leases/rentalagreement_form.html"
    success_url = reverse_lazy("rentalagreement_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class RentalAgreementUpdateView(UpdateView):
    model = RentalAgreement
    form_class = RentalAgreementForm
    template_name = "leases/rentalagreement_form.html"
    success_url = reverse_lazy("rentalagreement_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class RentalAgreementDeleteView(DeleteView):
    model = RentalAgreement
    template_name = "leases/rentalagreement_confirm_delete.html"
    success_url = reverse_lazy("rentalagreement_list")


def rental_agreement_details(request, pk: int):
    """Return JSON with fee details for a RentalAgreement.

    Used by the Payment form to autofill amounts based on the selected agreement.
    """
    try:
        ra = RentalAgreement.objects.select_related("tenant", "unit").get(pk=pk)
    except RentalAgreement.DoesNotExist:
        raise Http404("Rental agreement not found")

    data = {
        "id": ra.id,
        "tenant": str(ra.tenant) if getattr(ra, "tenant", None) else None,
        "unit": str(ra.unit) if getattr(ra, "unit", None) else None,
        "base_rent": float(ra.base_rent or 0.0),
        "coop_fee": float(ra.coop_fee or 0.0),
        "electricity": float(ra.electricity or 0.0),
        "gas": float(ra.gas or 0.0),
        "other_fees": float(ra.other_fees or 0.0),
    }
    return JsonResponse(data)
