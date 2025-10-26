from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse, HttpRequest
from calendar import month_name
from .models import Payment
from .forms import PaymentForm
from .tax import compute_tax_for_payment


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
        total_tax = 0.0
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
            total_income += float(p.base_rent or 0.0)
            total_tax += float(getattr(p, "tax_amount", 0.0) or 0.0)

        from .forms import PaymentForm
        payment_form = PaymentForm()

        ctx.update(
            {
                "year": year,
                "month": month,
                "grouped": grouped,
                "total_income": total_income,
                "total_tax": total_tax,
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
        # Subtotal before tax (excluding water)
        subtotal = (
            float(obj.base_rent or 0.0)
            + float(obj.coop_fee or 0.0)
            + float(obj.electricity or 0.0)
            + float(obj.gas or 0.0)
            + float(obj.other_fees or 0.0)
        )
        # Compute tax on base_rent according to business rules
        rate, amount = compute_tax_for_payment(obj)
        obj.tax_rate = float(rate or 0.0)
        obj.tax_amount = float(amount or 0.0)
        obj.total_amount = subtotal + obj.tax_amount
        obj.save()
        # Redirect back to monthly page of the due date
        due = obj.date_due
        return redirect(f"{reverse('payments_monthly')}?year={due.year}&month={due.month}")

class PaymentUpdateView(UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payment_form.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.water = 0.0
        subtotal = (
            float(obj.base_rent or 0.0)
            + float(obj.coop_fee or 0.0)
            + float(obj.electricity or 0.0)
            + float(obj.gas or 0.0)
            + float(obj.other_fees or 0.0)
        )
        rate, amount = compute_tax_for_payment(obj)
        obj.tax_rate = float(rate or 0.0)
        obj.tax_amount = float(amount or 0.0)
        obj.total_amount = subtotal + obj.tax_amount
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


def payments_report_pdf(request: HttpRequest) -> HttpResponse:
    """Generate a PDF report for payments within a given year or month range.

    Query params (GET):
      - year: integer (required)
      - full_year: optional flag ("1", "true") to indicate whole year
      - start_month: 1-12 (optional if full_year)
      - end_month: 1-12 (optional if full_year)

    The report shows, per month:
      - number of payments
      - income (sum of base_rent)
      - tax to pay (sum of tax_amount)
      - total amount (sum of total_amount)
    and grand totals for the selected period.
    """
    import io
    from datetime import date, timedelta

    # Lazy import of reportlab to avoid import-time errors if not installed in some environments
    try:
        from reportlab.pdfgen import canvas  # type: ignore
        from reportlab.lib.pagesizes import A4, landscape  # type: ignore
        from reportlab.lib.units import mm  # type: ignore
    except Exception as e:  # pragma: no cover - handled at runtime
        return HttpResponse(f"PDF generation library missing: {e}", status=500)

    # Parse and validate inputs
    today = timezone.now().date()
    try:
        year = int(request.GET.get("year", today.year))
    except Exception:
        year = today.year

    full_year_flag = str(request.GET.get("full_year", "")).lower() in {"1", "true", "yes"}

    def _to_int(val, default=None):
        try:
            return int(val)
        except Exception:
            return default

    start_month = _to_int(request.GET.get("start_month"), None)
    end_month = _to_int(request.GET.get("end_month"), None)

    if full_year_flag or not start_month or not end_month:
        start_month, end_month = 1, 12

    # Clamp and ensure order
    start_month = max(1, min(12, int(start_month)))
    end_month = max(1, min(12, int(end_month)))
    if start_month > end_month:
        start_month, end_month = end_month, start_month

    # Determine date range
    start_date = date(year, start_month, 1)
    # Compute last day of end_month
    if end_month == 12:
        end_date = date(year, 12, 31)
    else:
        end_date = date(year, end_month + 1, 1) - timedelta(days=1)

    # Fetch payments in range (based on date_due)
    qs = (
        Payment.objects.filter(
            date_due__gte=start_date,
            date_due__lte=end_date,
        )
        .select_related(
            "rental_agreement",
            "rental_agreement__property",
            "rental_agreement__tenant",
        )
        .order_by("date_due")
    )

    # Aggregate per month
    per_month = {}
    grand = {
        "count": 0,
        "income": 0.0,
        "tax": 0.0,
        "total": 0.0,
    }

    for p in qs:
        m = int(p.date_due.month)
        per = per_month.setdefault(
            m,
            {"count": 0, "income": 0.0, "tax": 0.0, "total": 0.0},
        )
        per["count"] += 1
        per["income"] += float(getattr(p, "base_rent", 0.0) or 0.0)
        per["tax"] += float(getattr(p, "tax_amount", 0.0) or 0.0)
        per["total"] += float(getattr(p, "total_amount", 0.0) or 0.0)
        grand["count"] += 1
        grand["income"] += float(getattr(p, "base_rent", 0.0) or 0.0)
        grand["tax"] += float(getattr(p, "tax_amount", 0.0) or 0.0)
        grand["total"] += float(getattr(p, "total_amount", 0.0) or 0.0)

    # Prepare PDF
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    title = "Payments Report"
    period = (
        f"Year {year}" if (start_month == 1 and end_month == 12) else f"{month_name[start_month]}–{month_name[end_month]} {year}"
    )

    x_margin = 20 * mm
    y = height - 25 * mm
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(x_margin, y, title)
    pdf.setFont("Helvetica", 11)
    y -= 8 * mm
    pdf.drawString(x_margin, y, f"Period: {period}")

    # Table header
    y -= 10 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x_margin, y, "Month")
    pdf.drawRightString(x_margin + 100 * mm, y, "Payments")
    pdf.drawRightString(x_margin + 140 * mm, y, "Income")
    pdf.drawRightString(x_margin + 170 * mm, y, "Tax")
    pdf.drawRightString(x_margin + 200 * mm, y, "Total")

    pdf.setFont("Helvetica", 11)
    y -= 6 * mm

    # Rows for each month in the selected range
    for m in range(start_month, end_month + 1):
        data = per_month.get(m, {"count": 0, "income": 0.0, "tax": 0.0, "total": 0.0})
        pdf.drawString(x_margin, y, f"{month_name[m]}")
        pdf.drawRightString(x_margin + 100 * mm, y, f"{data['count']}")
        pdf.drawRightString(x_margin + 140 * mm, y, f"{data['income']:.2f}")
        pdf.drawRightString(x_margin + 170 * mm, y, f"{data['tax']:.2f}")
        pdf.drawRightString(x_margin + 200 * mm, y, f"{data['total']:.2f}")
        y -= 6 * mm
        if y < 30 * mm:
            pdf.showPage()
            y = height - 25 * mm
            pdf.setFont("Helvetica", 11)

    # Totals
    y -= 4 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x_margin, y, "Totals")
    pdf.drawRightString(x_margin + 100 * mm, y, f"{grand['count']}")
    pdf.drawRightString(x_margin + 140 * mm, y, f"{grand['income']:.2f}")
    pdf.drawRightString(x_margin + 170 * mm, y, f"{grand['tax']:.2f}")
    pdf.drawRightString(x_margin + 200 * mm, y, f"{grand['total']:.2f}")

    pdf.save()

    buffer.seek(0)
    filename = (
        f"payments_report_{year}_full_year.pdf"
        if (start_month == 1 and end_month == 12)
        else f"payments_report_{year}_{start_month:02d}_{end_month:02d}.pdf"
    )
    resp = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = f"attachment; filename=\"{filename}\""
    return resp