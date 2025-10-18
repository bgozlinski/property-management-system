from django.views.generic import TemplateView, ListView, CreateView
from django.utils import timezone
from django.db.models import Sum, F
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import Payment
from .forms import PaymentForm


class DashboardView(TemplateView):
    template_name = 'dashboard.html'


class PaymentsMonthlyView(TemplateView):
    template_name = 'payments_monthly.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()
        year = int(self.request.GET.get("year", today.year))
        month = int(self.request.GET.get("month", today.month))

        qs = (
            Payment.objects.select_related(
                "rental_agreement",
                "rental_agreement__property",
                "rental_agreement__tenant",
            )
            .filter(date_due__year=year, date_due__month=month)
        )

        # Group payments by property then by tenant
        grouped = {}
        total_income = 0.0
        for p in qs:
            prop = p.rental_agreement.property
            tenant = p.rental_agreement.tenant
            key_prop = prop.id if prop else "unassigned"
            if key_prop not in grouped:
                grouped[key_prop] = {
                    "property": prop,
                    "tenants": {},
                    "property_total": 0.0,
                }
            tenants_map = grouped[key_prop]["tenants"]
            if tenant.id not in tenants_map:
                tenants_map[tenant.id] = {
                    "tenant": tenant,
                    "payments": [],
                    "tenant_total": 0.0,
                }
            tenants_map[tenant.id]["payments"].append(p)
            tenants_map[tenant.id]["tenant_total"] += float(p.total_amount)
            grouped[key_prop]["property_total"] += float(p.total_amount)
            total_income += float(p.total_amount)

        from .forms import PaymentForm
        payment_form = PaymentForm()

        ctx.update(
            {
                "year": year,
                "month": month,
                "grouped": grouped,
                "total_income": total_income,
                "payment_form": payment_form,
            }
        )
        return ctx


class TenantPaymentsView(TemplateView):
    template_name = 'payments_tenant.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = getattr(self.request, 'user', None)
        payments = []
        tenant = None
        if user and user.is_authenticated and getattr(user, 'role', None) == 1:
            # Load payments for the logged-in tenant
            from users.models import Tenant as TenantModel
            try:
                tenant = TenantModel.objects.select_related('user').get(user=user)
            except TenantModel.DoesNotExist:
                tenant = None
            if tenant:
                payments = (
                    Payment.objects.select_related('rental_agreement')
                    .filter(rental_agreement__tenant=tenant)
                    .order_by('-date_due')
                )
        ctx.update({
            'tenant': tenant,
            'payments': payments,
        })
        return ctx


class PaymentCreateView(CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payment_form.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        # Ensure hidden 'water' field is set to 0.0 since it's excluded from the form
        obj.water = 0.0
        # Compute total amount excluding water
        obj.total_amount = (
            float(obj.base_rent or 0.0)
            + float(obj.coop_fee or 0.0)
            + float(obj.electricity or 0.0)
            + float(obj.gas or 0.0)
            + float(obj.other_fees or 0.0)
        )
        obj.save()
        # Redirect back to monthly page of the due date
        due = obj.date_due
        return redirect(f"{reverse('payments_monthly')}?year={due.year}&month={due.month}")


from django.views.generic import UpdateView, DeleteView

class PaymentUpdateView(UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payment_form.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.water = 0.0
        obj.total_amount = (
            float(obj.base_rent or 0.0)
            + float(obj.coop_fee or 0.0)
            + float(obj.electricity or 0.0)
            + float(obj.gas or 0.0)
            + float(obj.other_fees or 0.0)
        )
        obj.save()
        due = obj.date_due
        return redirect(f"{reverse('payments_monthly')}?year={due.year}&month={due.month}")

class PaymentDeleteView(DeleteView):
    model = Payment
    template_name = 'payment_confirm_delete.html'

    def get_success_url(self):
        # After deletion, return to the monthly page for the payment's due date
        # self.object still has values during get_success_url
        due = getattr(self.object, 'date_due', None)
        if due:
            return f"{reverse('payments_monthly')}?year={due.year}&month={due.month}"
        return reverse('payments_monthly')