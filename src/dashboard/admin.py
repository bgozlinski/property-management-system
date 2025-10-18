from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "rental_agreement",
        "date_due",
        "date_paid",
        "total_amount",
        "status",
    )
    list_filter = ("status", "date_due", "rental_agreement__property", "rental_agreement__tenant")
    search_fields = (
        "rental_agreement__property__address",
        "rental_agreement__property__city",
        "rental_agreement__tenant__name",
    )
