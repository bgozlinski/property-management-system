import factory
from django.utils import timezone
from .models import MaintenanceRequest
from properties.factories import PropertyFactory
from users.factories import TenantFactory


class MaintenanceRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MaintenanceRequest

    property = factory.SubFactory(PropertyFactory)
    tenant = factory.SubFactory(TenantFactory)
    description = factory.Faker('paragraph')
    status = MaintenanceRequest.StatusChoices.PENDING
    created_at = factory.LazyFunction(timezone.now)
    resolved_at = None
    