import factory
from .models import CustomUser, Landlord, Tenant

class CustomUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

    email = factory.LazyAttribute(lambda obj: f'{obj.first_name}.{obj.last_name}@example.com')

    password = factory.PostGenerationMethodCall('set_password', 'password123')

    role = CustomUser.RoleChoices.TENANT

    is_active = True
    is_staff = False
    is_superuser = False


class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant

    user = factory.SubFactory(CustomUserFactory, role=CustomUser.RoleChoices.TENANT)
    contact_info = factory.Faker('phone_number')


class LandlordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Landlord

    user = factory.SubFactory(CustomUserFactory, role=CustomUser.RoleChoices.LANDLORD)
    contact_info = factory.Faker('phone_number')