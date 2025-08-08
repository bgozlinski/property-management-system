import factory
from django.utils import timezone
from .models import Payment
from leases.factories import RentalAgreementFactory


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    rental_agreement = factory.SubFactory(RentalAgreementFactory)
    date_due = factory.LazyFunction(lambda: timezone.now().date())
    date_paid = None
    base_rent = factory.Faker("pyfloat", min_value=500, max_value=5000)
    coop_fee = factory.Faker("pyfloat", min_value=50, max_value=500)
    electricity = factory.Faker("pyfloat", min_value=20, max_value=200)
    water = factory.Faker("pyfloat", min_value=10, max_value=100)
    gas = factory.Faker("pyfloat", min_value=10, max_value=100)
    other_fees = factory.Faker("pyfloat", min_value=0, max_value=200)
    total_amount = factory.LazyAttribute(
        lambda o: o.base_rent
        + o.coop_fee
        + o.electricity
        + o.water
        + o.gas
        + o.other_fees
    )
    status = Payment.StatusChoices.PENDING
    invoice_url = factory.Faker("url")
