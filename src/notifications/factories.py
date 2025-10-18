import factory
import uuid
from django.utils import timezone
from .models import Reminder, TenantInvitation
from properties.factories import PropertyFactory
from properties.models import Building, Unit
from users.factories import CustomUserFactory


"""
This module provides factory classes for creating test instances of notification models.

These factories are used in tests to generate realistic test data for reminders
and tenant invitations with minimal setup.
"""


def _ensure_unit_from_property(prop):
    """Create and return a Unit mapped from a legacy Property instance.

    This provides backward compatibility for tests and code paths that still
    pass a `property` kwarg while the Reminder model now requires a `unit`.
    """
    # Create a Building that mirrors the legacy Property address data
    building = Building.objects.create(
        landlord=prop.landlord,
        name=str(prop.address),
        address=prop.address,
        city=prop.city,
        postal_code=prop.postal_code,
    )
    # Create a simple Unit within that Building; reuse area if available
    area = getattr(prop, "area_m2", 0) or 0
    unit = Unit.objects.create(
        building=building,
        number="1",
        floor=0,
        area_m2=area,
    )
    return unit


class ReminderFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating Reminder instances for testing.

    Generates reminders with realistic titles, descriptions, and due dates
    set 30 days in the future. Ensures a Unit is provided, while accepting
    a legacy `property` kwarg for backward compatibility (it will create a
    Building+Unit reflecting that Property).
    """

    class Meta:
        model = Reminder

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    due_date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=30))

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        # Map legacy `property` kwarg to a Unit
        legacy_prop = kwargs.pop("property", None)
        if "unit" not in kwargs:
            if legacy_prop is not None:
                kwargs["unit"] = _ensure_unit_from_property(legacy_prop)
            else:
                # Create a default unit under a fresh building/landlord
                prop = PropertyFactory()
                kwargs["unit"] = _ensure_unit_from_property(prop)
        instance = model_class(*args, **kwargs)
        # Attach a compatibility attribute so tests can access reminder.property
        if legacy_prop is not None:
            setattr(instance, "property", legacy_prop)
        return instance

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Map legacy `property` kwarg to a Unit
        legacy_prop = kwargs.pop("property", None)
        if "unit" not in kwargs:
            if legacy_prop is not None:
                kwargs["unit"] = _ensure_unit_from_property(legacy_prop)
            else:
                prop = PropertyFactory()
                kwargs["unit"] = _ensure_unit_from_property(prop)
        instance = model_class._default_manager.create(*args, **kwargs)
        if legacy_prop is not None:
            setattr(instance, "property", legacy_prop)
        return instance


class TenantInvitationFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating TenantInvitation instances for testing.

    Generates invitations with random email addresses, associated with a
    randomly generated property and landlord. Invitations are set to expire
    7 days in the future and have a PENDING status by default.
    """

    class Meta:
        model = TenantInvitation

    email = factory.Faker("email")
    # For backward compatibility, map a generated Property to a Unit
    property_unit = factory.LazyFunction(lambda: _ensure_unit_from_property(PropertyFactory()))
    landlord = factory.SubFactory(CustomUserFactory, role=2)
    created_at = factory.LazyFunction(timezone.now)
    expires_at = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=7))
    token = factory.LazyFunction(uuid.uuid4)
    status = TenantInvitation.StatusChoices.PENDING
