from django.contrib import admin

from .models import RentalAgreement


@admin.register(RentalAgreement)
class RentalAgreementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "property",
        "unit",
        "tenant",
        "start_date",
        "end_date",
        "base_rent",
        "coop_fee",
        "electricity",
        "gas",
        "other_fees",
    )
    list_filter = ("property", "unit", "tenant")
    search_fields = (
        "property__address",
        "property__city",
        "tenant__name",
    )
