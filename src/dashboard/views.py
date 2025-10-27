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
    """Display the main application dashboard.

    For landlord users, the context includes quick KPIs:
    - rented_units: number of units currently marked as rented
    - free_units: number of units marked as available
    - pending_payments: count of pending or overdue payments
    - tax_previous_month: sum of tax to pay for the previous calendar month
    """
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = getattr(self.request, "user", None)
        try:
            from users.models import CustomUser, Landlord  # type: ignore
            from properties.models import Unit  # type: ignore
            from django.db.models import Q, Sum  # type: ignore
            from django.utils import timezone  # type: ignore
        except Exception:
            return ctx

        if not (user and getattr(user, "is_authenticated", False)):
            return ctx

        # Only compute landlord metrics for landlord users
        role_landlord = getattr(CustomUser.RoleChoices, "LANDLORD", 2)
        if getattr(user, "role", None) != role_landlord:
            return ctx

        try:
            landlord = Landlord.objects.select_related("user").get(user=user)
        except Landlord.DoesNotExist:
            return ctx

        # Units owned by landlord
        units_qs = Unit.objects.filter(building__landlord=landlord)
        rented_units = units_qs.filter(status=Unit.Status.RENTED).count()
        free_units = units_qs.filter(status=Unit.Status.AVAILABLE).count()

        # Pending or overdue payments for landlord
        payments_qs = (
            Payment.objects.filter(
                Q(rental_agreement__property__landlord=landlord)
                | Q(rental_agreement__unit__building__landlord=landlord)
            )
        )
        pending_payments = payments_qs.filter(
            status__in=[Payment.StatusChoices.PENDING, Payment.StatusChoices.OVERDUE]
        ).count()

        # Previous calendar month tax to pay (based on date_due)
        today = timezone.now().date()
        if today.month == 1:
            prev_year, prev_month = today.year - 1, 12
        else:
            prev_year, prev_month = today.year, today.month - 1

        tax_prev_month = (
            payments_qs.filter(date_due__year=prev_year, date_due__month=prev_month)
            .aggregate(total=Sum("tax_amount"))
            .get("total")
            or 0.0
        )

        ctx["landlord_metrics"] = {
            "rented_units": rented_units,
            "free_units": free_units,
            "pending_payments": pending_payments,
            "tax_previous_month": float(tax_prev_month or 0.0),
            "tax_previous_month_display": f"{float(tax_prev_month or 0.0):.2f}",
        }
        return ctx


class PaymentsMonthlyView(TemplateView):
    """Monthly payments dashboard grouped by property with totals (no tenant split)."""
    template_name = 'payments_monthly.html'

    def get_context_data(self, **kwargs):
        """Build context grouped by property and compute monthly totals."""
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

        grouped = {}
        total_income = 0.0
        total_tax = 0.0
        for p in qs:
            ra = getattr(p, "rental_agreement", None)
            prop = getattr(ra, "property", None) if ra else None
            key_prop = prop.id if prop else "unassigned"
            if key_prop not in grouped:
                grouped[key_prop] = {
                    "property": prop,
                    "payments": [],
                    "property_total": 0.0,
                }
            grouped[key_prop]["payments"].append(p)
            grouped[key_prop]["property_total"] += float(getattr(p, "total_amount", 0.0) or 0.0)
            total_income += float(getattr(p, "base_rent", 0.0) or 0.0)
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
    """Display payments belonging to the currently logged-in tenant."""
    template_name = 'payments_tenant.html'

    def get_context_data(self, **kwargs):
        """Return context with tenant object and their payments ordered by due date."""
        ctx = super().get_context_data(**kwargs)
        user = getattr(self.request, 'user', None)
        payments = []
        tenant = None
        if user and user.is_authenticated and getattr(user, 'role', None) == 1:
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
    """Create a new payment and compute totals and tax before saving."""
    model = Payment
    form_class = PaymentForm
    template_name = 'payment_form.html'

    def form_valid(self, form):
        """Populate derived fields (water, subtotal, tax, total) and redirect to the month view."""
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

class PaymentUpdateView(UpdateView):
    """Update an existing payment and recompute derived fields before saving."""
    model = Payment
    form_class = PaymentForm
    template_name = 'payment_form.html'

    def form_valid(self, form):
        """Recalculate subtotal, tax, and total, then redirect to the month view."""
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
    """Delete a payment and redirect back to its due month list."""
    model = Payment
    template_name = 'payment_confirm_delete.html'

    def get_success_url(self):
        """Return the monthly listing URL for the deleted payment's due date, if available."""
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