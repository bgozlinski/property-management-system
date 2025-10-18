from datetime import date
from calendar import monthrange

from django.core.management.base import BaseCommand
from django.db import transaction

from leases.models import RentalAgreement
from dashboard.models import Payment


class Command(BaseCommand):
    help = "Generate monthly Payment records from active RentalAgreements for a given year and month."

    def add_arguments(self, parser):
        parser.add_argument("year", type=int, help="Year for which to generate payments")
        parser.add_argument("month", type=int, help="Month (1-12) for which to generate payments")
        parser.add_argument(
            "--due-day",
            type=int,
            default=5,
            help="Day of the month to set as due date (default: 5)",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="If provided, existing payments for the target month will be overwritten",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        year = options["year"]
        month = options["month"]
        due_day = max(1, min(options["due_day"], monthrange(year, month)[1]))
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])
        due_date = date(year, month, due_day)

        qs = RentalAgreement.objects.select_related("property", "tenant")

        created = 0
        updated = 0

        for ra in qs:
            # Active if start_date is not after the month and (no end or end_date not before month)
            if ra.start_date and ra.start_date > last_day:
                continue
            if ra.end_date and ra.end_date < first_day:
                continue

            defaults = {
                "base_rent": float(ra.base_rent or 0.0),
                "coop_fee": float(ra.coop_fee or 0.0),
                "electricity": float(ra.electricity or 0.0),
                "water": 0.0,  # RentalAgreement has no water field defined; default to 0
                "gas": float(ra.gas or 0.0),
                "other_fees": float(ra.other_fees or 0.0),
            }
            defaults["total_amount"] = (
                defaults["base_rent"]
                + defaults["coop_fee"]
                + defaults["electricity"]
                + defaults["gas"]
                + defaults["other_fees"]
            )

            if options["overwrite"]:
                obj, created_flag = Payment.objects.update_or_create(
                    rental_agreement=ra,
                    date_due=due_date,
                    defaults=defaults,
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1
            else:
                obj, created_flag = Payment.objects.get_or_create(
                    rental_agreement=ra,
                    date_due=due_date,
                    defaults=defaults,
                )
                if created_flag:
                    created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Payments generated for {year}-{month:02d}: created={created}, updated={updated}"
            )
        )
