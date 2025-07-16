import factory
import uuid
from django.utils import timezone
from .models import Reminder, TenantInvitation
from properties.factories import PropertyFactory
from users.factories import CustomUserFactory


class ReminderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reminder

    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('paragraph')
    due_date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=30))
    property = factory.SubFactory(PropertyFactory)


class TenantInvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TenantInvitation

    email = factory.Faker('email')
    property_unit = factory.SubFactory(PropertyFactory)
    landlord = factory.SubFactory(CustomUserFactory, role=2)
    created_at = factory.LazyFunction(timezone.now)
    expires_at = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=7))
    token = factory.LazyFunction(uuid.uuid4)
    status = TenantInvitation.StatusChoices.PENDING
