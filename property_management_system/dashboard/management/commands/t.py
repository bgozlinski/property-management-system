from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import random
from datetime import timedelta
from users.factories import CustomUserFactory, TenantFactory, LandlordFactory
from properties.factories import PropertyFactory
from notifications.factories import ReminderFactory, TenantInvitationFactory
from leases.factories import RentalAgreementFactory
from maintenance.factories import MaintenanceRequestFactory
from dashboard.factories import PaymentFactory
from properties.models import Property
from notifications.models import TenantInvitation
from maintenance.models import MaintenanceRequest
from dashboard.models import Payment


class Command(BaseCommand):
    help = "Generates realistic sample data for development purposes"

    def add_arguments(self, parser):
        parser.add_argument(
            '--landlords',
            type=int,
            default=5,
            help='Number of landlords to create'
        )
        parser.add_argument(
            '--tenants',
            type=int,
            default=20,
            help='Number of tenants to create'
        )
        parser.add_argument(
            '--properties',
            type=int,
            default=30,
            help='Number of properties to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        num_landlords = options['landlords']
        num_tenants = options['tenants']
        num_properties = options['properties']
        clear_data = options['clear']

        if clear_data:
            self.clear_existing_data()
            self.stdout.write(self.style.SUCCESS('Existing data cleared successfully'))

        self.stdout.write(f"Creating {num_landlords} landlords...")
        landlords = []
        for i in range(num_landlords):
            landlord = LandlordFactory.create()
            landlord.name = f"{landlord.user.first_name} {landlord.user.last_name}"
            landlord.save()
            landlords.append(landlord)
        self.stdout.write(self.style.SUCCESS(f'Created {num_landlords} landlords'))

        self.stdout.write(f"Creating {num_properties} properties...")
        properties = []
        for i in range(num_properties):
            landlord = random.choice(landlords)
            property = PropertyFactory.create(
                landlord=landlord,
                status=random.choice([
                    Property.StatusChoices.AVAILABLE,
                    Property.StatusChoices.RENTED,
                    Property.StatusChoices.MAINTENANCE,
                    Property.StatusChoices.UNAVAILABLE
                ])
            )
            properties.append(property)
        self.stdout.write(self.style.SUCCESS(f'Created {num_properties} properties'))

        self.stdout.write(f"Creating {num_tenants} tenants...")
        tenants = []
        for i in range(num_tenants):
            tenant = TenantFactory.create()
            tenant.name = f"{tenant.user.first_name} {tenant.user.last_name}"
            tenant.save()
            tenants.append(tenant)
        self.stdout.write(self.style.SUCCESS(f'Created {num_tenants} tenants'))

        self.stdout.write("Creating rental agreements...")
        rental_agreements = []
        rented_properties = [p for p in properties if p.status == Property.StatusChoices.RENTED]

        for property in rented_properties:
            tenant = random.choice(tenants)
            start_date = timezone.now().date() - timedelta(days=random.randint(30, 365))
            end_date = start_date + timedelta(days=random.randint(180, 730))

            agreement = RentalAgreementFactory.create(
                property=property,
                tenant=tenant,
                start_date=start_date,
                end_date=end_date,
                base_rent=property.current_rent
            )
            rental_agreements.append(agreement)

        self.stdout.write(self.style.SUCCESS(f'Created {len(rental_agreements)} rental agreements'))

        self.stdout.write("Creating maintenance requests...")
        maintenance_requests = []
        for _ in range(random.randint(10, 30)):
            if not rental_agreements:
                break

            agreement = random.choice(rental_agreements)
            status = random.choice(list(MaintenanceRequest.StatusChoices))

            request = MaintenanceRequestFactory.create(
                property=agreement.property,
                tenant=agreement.tenant,
                status=status,
                resolved_at=timezone.now() if status == MaintenanceRequest.StatusChoices.COMPLETED else None
            )
            maintenance_requests.append(request)

        self.stdout.write(self.style.SUCCESS(f'Created {len(maintenance_requests)} maintenance requests'))

        self.stdout.write("Creating payments...")
        payments = []
        for agreement in rental_agreements:
            for i in range(1, random.randint(3, 12)):
                date_due = agreement.start_date + timedelta(days=30 * i)
                if date_due > timezone.now().date():
                    continue

                status = random.choice([
                    Payment.StatusChoices.PAID,
                    Payment.StatusChoices.PAID,
                    Payment.StatusChoices.OVERDUE
                ])

                date_paid = date_due + timedelta(
                    days=random.randint(-5, 15)) if status == Payment.StatusChoices.PAID else None

                payment = PaymentFactory.create(
                    rental_agreement=agreement,
                    date_due=date_due,
                    date_paid=date_paid,
                    base_rent=agreement.base_rent,
                    status=status
                )
                payments.append(payment)

            next_payment_date = max([p.date_due for p in payments if p.rental_agreement == agreement],
                                    default=agreement.start_date) + timedelta(days=30)
            if next_payment_date < agreement.end_date:
                payment = PaymentFactory.create(
                    rental_agreement=agreement,
                    date_due=next_payment_date,
                    date_paid=None,
                    base_rent=agreement.base_rent,
                    status=Payment.StatusChoices.PENDING
                )
                payments.append(payment)

        self.stdout.write(self.style.SUCCESS(f'Created {len(payments)} payments'))

        self.stdout.write("Creating reminders...")
        reminders = []
        for landlord in landlords:
            landlord_properties = [p for p in properties if p.landlord == landlord]
            for property in landlord_properties:
                for _ in range(random.randint(0, 3)):
                    reminder = ReminderFactory.create(
                        property=property,
                        due_date=timezone.now() + timedelta(days=random.randint(1, 90))
                    )
                    reminders.append(reminder)

        self.stdout.write(self.style.SUCCESS(f'Created {len(reminders)} reminders'))

        self.stdout.write("Creating tenant invitations...")
        invitations = []
        available_properties = [p for p in properties if p.status == Property.StatusChoices.AVAILABLE]

        for property in available_properties[:min(10, len(available_properties))]:
            status = random.choice(list(TenantInvitation.StatusChoices))

            invitation = TenantInvitationFactory.create(
                property_unit=property,
                landlord=property.landlord.user,
                status=status
            )
            invitations.append(invitation)

        self.stdout.write(self.style.SUCCESS(f'Created {len(invitations)} tenant invitations'))

        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Sample data generation complete!'))
        self.stdout.write(self.style.SUCCESS(f'Created:'))
        self.stdout.write(self.style.SUCCESS(f'- {num_landlords} landlords'))
        self.stdout.write(self.style.SUCCESS(f'- {num_tenants} tenants'))
        self.stdout.write(self.style.SUCCESS(f'- {num_properties} properties'))
        self.stdout.write(self.style.SUCCESS(f'- {len(rental_agreements)} rental agreements'))
        self.stdout.write(self.style.SUCCESS(f'- {len(maintenance_requests)} maintenance requests'))
        self.stdout.write(self.style.SUCCESS(f'- {len(payments)} payments'))
        self.stdout.write(self.style.SUCCESS(f'- {len(reminders)} reminders'))
        self.stdout.write(self.style.SUCCESS(f'- {len(invitations)} tenant invitations'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

    def clear_existing_data(self):
        """Clear all existing data from the database"""
        from users.models import Tenant, Landlord
        from properties.models import Property
        from notifications.models import Reminder, TenantInvitation
        from leases.models import RentalAgreement
        from maintenance.models import MaintenanceRequest
        from dashboard.models import Payment

        Payment.objects.all().delete()
        MaintenanceRequest.objects.all().delete()
        RentalAgreement.objects.all().delete()
        Reminder.objects.all().delete()
        TenantInvitation.objects.all().delete()
        Property.objects.all().delete()
        Tenant.objects.all().delete()
        Landlord.objects.all().delete()
