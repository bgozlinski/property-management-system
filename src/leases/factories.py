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
    property = factory.SubFactory(PropertyFactory)
    tenant = factory.SubFactory(TenantFactory)
