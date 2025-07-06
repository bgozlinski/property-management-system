from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import Property
from .forms import PropertyForm
from users.models import Landlord

User = get_user_model()


class PropertyModelTest(TestCase):
    """Tests for the Property model"""

    def setUp(self):
        # Create a test user with landlord role
        self.user = User.objects.create_user(
            email='landlord@test.com',
            password='testpassword',
            role=User.RoleChoices.LANDLORD
        )
        self.landlord = Landlord.objects.create(user=self.user)

        # Create a test property
        self.property = Property.objects.create(
            address='123 Test St',
            city='Test City',
            postal_code='12345',
            area_m2=100.0,
            current_rent=1000.0,
            additional_costs=200.0,
            status=Property.StatusChoices.AVAILABLE,
            landlord=self.landlord
        )

    def test_property_creation(self):
        """Test that a property can be created with all required fields"""
        self.assertEqual(self.property.address, '123 Test St')
        self.assertEqual(self.property.city, 'Test City')
        self.assertEqual(self.property.postal_code, '12345')
        self.assertEqual(self.property.area_m2, 100.0)
        self.assertEqual(self.property.current_rent, 1000.0)
        self.assertEqual(self.property.additional_costs, 200.0)
        self.assertEqual(self.property.status, Property.StatusChoices.AVAILABLE)
        self.assertEqual(self.property.landlord, self.landlord)

    def test_property_string_representation(self):
        """Test the string representation of a property"""
        expected_str = f"{self.property.address}, {self.property.city}"
        self.assertEqual(str(self.property), expected_str)


class PropertyFormTest(TestCase):
    """Tests for the PropertyForm"""

    def setUp(self):
        # Create a test user with landlord role
        self.user = User.objects.create_user(
            email='landlord@test.com',
            password='testpassword',
            role=User.RoleChoices.LANDLORD
        )
        self.landlord = Landlord.objects.create(user=self.user)

    def test_valid_form(self):
        """Test that the form is valid with all required fields"""
        form_data = {
            'address': '123 Test St',
            'city': 'Test City',
            'postal_code': '12345',
            'area_m2': 100.0,
            'current_rent': 1000.0,
            'additional_costs': 200.0,
            'status': Property.StatusChoices.AVAILABLE
        }
        form = PropertyForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self):
        """Test that the form is invalid when required fields are missing"""
        form_data = {
            'address': '123 Test St',
            # Missing other required fields
        }
        form = PropertyForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 6)  # 6 missing fields


class PropertyViewsTest(TestCase):
    """Tests for the property views"""

    def setUp(self):
        # Create a test user with landlord role
        self.user = User.objects.create_user(
            email='landlord@test.com',
            password='testpassword',
            role=User.RoleChoices.LANDLORD
        )
        self.landlord = Landlord.objects.create(user=self.user)

        # Create a test property
        self.property = Property.objects.create(
            address='123 Test St',
            city='Test City',
            postal_code='12345',
            area_m2=100.0,
            current_rent=1000.0,
            additional_costs=200.0,
            status=Property.StatusChoices.AVAILABLE,
            landlord=self.landlord
        )

        # Set up the client
        self.client = Client()
        self.client.login(email='landlord@test.com', password='testpassword')

    def test_property_list_view(self):
        """Test the property_list view"""
        response = self.client.get(reverse('property_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'property_list.html')
        self.assertEqual(len(response.context['properties']), 1)
        self.assertIsInstance(response.context['form'], PropertyForm)

    def test_property_detail_view_get(self):
        """Test the property_detail view GET request"""
        response = self.client.get(reverse('property_detail', args=[self.property.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'property_detail.html')
        self.assertEqual(response.context['property'], self.property)
        self.assertIsInstance(response.context['form'], PropertyForm)

    def test_property_detail_view_post(self):
        """Test the property_detail view POST request"""
        form_data = {
            'address': '456 Updated St',
            'city': 'Updated City',
            'postal_code': '67890',
            'area_m2': 200.0,
            'current_rent': 2000.0,
            'additional_costs': 300.0,
            'status': Property.StatusChoices.RENTED
        }
        response = self.client.post(reverse('property_detail', args=[self.property.id]), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.property.refresh_from_db()
        self.assertEqual(self.property.address, '456 Updated St')
        self.assertEqual(self.property.city, 'Updated City')
        self.assertEqual(self.property.status, Property.StatusChoices.RENTED)

    def test_property_create_view_get(self):
        """Test the PropertyCreateView GET request"""
        response = self.client.get(reverse('add_property'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_property.html')
        self.assertIsInstance(response.context['form'], PropertyForm)

    def test_property_create_view_post(self):
        """Test the PropertyCreateView POST request"""
        form_data = {
            'address': '789 New St',
            'city': 'New City',
            'postal_code': '54321',
            'area_m2': 150.0,
            'current_rent': 1500.0,
            'additional_costs': 250.0,
            'status': Property.StatusChoices.AVAILABLE
        }
        response = self.client.post(reverse('add_property'), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Property.objects.count(), 2)
        new_property = Property.objects.get(address='789 New St')
        self.assertEqual(new_property.city, 'New City')
        self.assertEqual(new_property.landlord, self.landlord)

    def test_property_update_view(self):
        """Test the PropertyUpdateView"""
        form_data = {
            'address': '321 Edit St',
            'city': 'Edit City',
            'postal_code': '98765',
            'area_m2': 120.0,
            'current_rent': 1200.0,
            'additional_costs': 220.0,
            'status': Property.StatusChoices.MAINTENANCE
        }
        response = self.client.post(reverse('edit_property', args=[self.property.id]), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.property.refresh_from_db()
        self.assertEqual(self.property.address, '321 Edit St')
        self.assertEqual(self.property.city, 'Edit City')
        self.assertEqual(self.property.status, Property.StatusChoices.MAINTENANCE)

    def test_property_delete_view(self):
        """Test the PropertyDeleteView"""
        response = self.client.post(reverse('delete_property', args=[self.property.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        self.assertEqual(Property.objects.count(), 0)


class PropertyAPITest(TestCase):
    """Tests for the Property API views"""

    def setUp(self):
        # Create a test user with landlord role
        self.user = User.objects.create_user(
            email='landlord@test.com',
            password='testpassword',
            role=User.RoleChoices.LANDLORD
        )
        self.landlord = Landlord.objects.create(user=self.user)

        # Create a test property
        self.property = Property.objects.create(
            address='123 Test St',
            city='Test City',
            postal_code='12345',
            area_m2=100.0,
            current_rent=1000.0,
            additional_costs=200.0,
            status=Property.StatusChoices.AVAILABLE,
            landlord=self.landlord
        )

        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_properties(self):
        """Test listing properties via API"""
        response = self.client.get(reverse('api_properties'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['address'], '123 Test St')

    def test_create_property(self):
        """Test creating a property via API"""
        data = {
            'address': '789 API St',
            'city': 'API City',
            'postal_code': '54321',
            'area_m2': 150.0,
            'current_rent': 1500.0,
            'additional_costs': 250.0,
            'status': Property.StatusChoices.AVAILABLE
        }
        response = self.client.post(reverse('api_properties'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Property.objects.count(), 2)
        new_property = Property.objects.get(address='789 API St')
        self.assertEqual(new_property.city, 'API City')

    def test_retrieve_property(self):
        """Test retrieving a single property via API"""
        response = self.client.get(reverse('api_property_detail', args=[self.property.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], '123 Test St')

    def test_update_property(self):
        """Test updating a property via API"""
        data = {
            'address': '456 Updated API St',
            'city': 'Updated API City',
            'postal_code': '67890',
            'area_m2': 200.0,
            'current_rent': 2000.0,
            'additional_costs': 300.0,
            'status': Property.StatusChoices.RENTED
        }
        response = self.client.put(reverse('api_property_detail', args=[self.property.id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.address, '456 Updated API St')
        self.assertEqual(self.property.city, 'Updated API City')

    def test_delete_property(self):
        """Test deleting a property via API"""
        response = self.client.delete(reverse('api_property_detail', args=[self.property.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Property.objects.count(), 0)