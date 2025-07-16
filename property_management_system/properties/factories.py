import factory
from .models import Property
from users.factories import LandlordFactory


class PropertyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Property

    address = factory.Faker('street_address')
    city = factory.Faker('city')
    postal_code = factory.Faker('postcode')
    area_m2 = factory.Faker('pyfloat', min_value=20, max_value=200)
    current_rent = factory.Faker('pyfloat', min_value=500, max_value=5000)
    additional_costs = factory.Faker('pyfloat', min_value=50, max_value=500)
    status = Property.StatusChoices.AVAILABLE
    landlord = factory.SubFactory(LandlordFactory)
