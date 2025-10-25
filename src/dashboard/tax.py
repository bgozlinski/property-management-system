from __future__ import annotations

from datetime import date
from typing import Tuple

from django.db.models import Sum, Q

from .models import Payment


LOW_RATE = 0.085  # 8.5%
HIGH_RATE = 0.125  # 12.5%
THRESHOLD_PLN = 100_000.0
POLAND_CODE = "PL"


def _get_landlord_from_payment(p: Payment):
    """Resolve the landlord for a payment via property first, then via unit->building.

    Returns None if neither path is available.
    """
    ra = getattr(p, "rental_agreement", None)
    if not ra:
        return None

    # Primary path: through the Property on the rental agreement
    prop = getattr(ra, "property", None)
    if prop:
        landlord = getattr(prop, "landlord", None)
        if landlord:
            return landlord

    # Fallback path: through Unit -> Building -> Landlord
    unit = getattr(ra, "unit", None)
    if unit:
        building = getattr(unit, "building", None)
        if building:
            landlord = getattr(building, "landlord", None)
            if landlord:
                return landlord

    return None


def _is_polish_resident(landlord) -> bool:
    try:
        code = (landlord.tax_residency_country or "").upper()
    except Exception:
        return False
    return code == POLAND_CODE


def _ytd_base_rent_before(p: Payment) -> float:
    """
    Sum base_rent of all payments for the same landlord in the same calendar year
    with due date strictly before this payment's due date.
    """
    landlord = _get_landlord_from_payment(p)
    if not landlord:
        return 0.0
    due: date = p.date_due
    if not due:
        return 0.0
    qs = Payment.objects.filter(
        Q(rental_agreement__property__landlord=landlord) |
        Q(rental_agreement__unit__building__landlord=landlord),
        date_due__year=due.year,
        date_due__lt=due,
    )
    # Exclude current instance if updating an existing payment
    if getattr(p, "pk", None):
        qs = qs.exclude(pk=p.pk)
    agg = qs.aggregate(total=Sum("base_rent")).get("total")
    return float(agg or 0.0)


def compute_tax_for_payment(p: Payment) -> Tuple[float, float]:
    """
    Compute the effective tax rate and tax amount for a given Payment according to rules:
    - Applies only if landlord's tax residency is PL.
    - Tax base is the payment's base_rent.
    - Per landlord, per calendar year tiering:
      * 8.5% on YTD base_rent up to 100,000 PLN
      * 12.5% on the portion exceeding 100,000 PLN
    - If the threshold is crossed in the current month, split the month's base_rent accordingly.

    Returns:
        (effective_rate, tax_amount)
        where effective_rate is a fraction (e.g., 0.085 for 8.5%).
    """
    landlord = _get_landlord_from_payment(p)
    if not landlord or not _is_polish_resident(landlord):
        return 0.0, 0.0

    base = float(getattr(p, "base_rent", 0.0) or 0.0)
    if base <= 0.0:
        return 0.0, 0.0

    ytd_before = _ytd_base_rent_before(p)

    remaining_low_band = max(0.0, THRESHOLD_PLN - ytd_before)
    taxed_at_low = min(base, remaining_low_band)
    taxed_at_high = max(0.0, base - taxed_at_low)

    tax_amount = taxed_at_low * LOW_RATE + taxed_at_high * HIGH_RATE
    effective_rate = tax_amount / base if base else 0.0
    return effective_rate, tax_amount
