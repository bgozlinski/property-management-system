import factory
from django.utils import timezone
from datetime import timedelta
from .models import RentalAgreement
from properties.factories import PropertyFactory
from users.factories import TenantFactory


class RentalAgreementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RentalAgreement

    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(lambda: (timezone.now() + timedelta(days=365)).date())

    base_rent = factory.Faker('pyfloat', min_value=500, max_value=5000)
    coop_fee = factory.Faker('pyfloat', min_value=50, max_value=500)
    electricity = factory.Faker('pyfloat', min_value=20, max_value=200)
    gas = factory.Faker('pyfloat', min_value=10, max_value=150)
    other_fees = factory.Faker('pyfloat', min_value=0, max_value=200)

    property = factory.SubFactory(PropertyFactory)
    tenant = factory.SubFactory(TenantFactory)
