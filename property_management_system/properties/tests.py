from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Property
from .forms import PropertyForm
from users.factories import LandlordFactory
from properties.factories import PropertyFactory
from http import HTTPStatus

User = get_user_model()


class PropertyModelTest(TestCase):
    """Tests for the Property model"""

    def setUp(self):
        self.landlord = LandlordFactory.create()
        self.user = self.landlord.user
        self.property = PropertyFactory.create(landlord=self.landlord)

    def test_property_creation(self):
        """Test that a property can be created with all required fields"""
        self.assertIsNotNone(self.property.address)
        self.assertIsNotNone(self.property.city)
        self.assertIsNotNone(self.property.postal_code)
        self.assertIsNotNone(self.property.area_m2)
        self.assertIsNotNone(self.property.current_rent)
        self.assertIsNotNone(self.property.additional_costs)
        self.assertIsNotNone(self.property.status)
        self.assertEqual(self.property.landlord, self.landlord)

    def test_property_string_representation(self):
        """Test the string representation of a property"""
        expected_str = f"{self.property.address}, {self.property.city}"
        self.assertEqual(str(self.property), expected_str)


class PropertyFormTest(TestCase):
    """Tests for the PropertyForm"""

    def setUp(self):
        self.landlord = LandlordFactory.create()
        self.user = self.landlord.user

    def test_valid_form(self):
        """Test that the form is valid with all required fields"""
        property_obj = PropertyFactory.build()

        form_data = {
            "address": property_obj.address,
            "city": property_obj.city,
            "postal_code": property_obj.postal_code,
            "area_m2": property_obj.area_m2,
            "current_rent": property_obj.current_rent,
            "additional_costs": property_obj.additional_costs,
            "status": property_obj.status,
        }
        form = PropertyForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self):
        """Test that the form is invalid when required fields are missing"""
        form_data = {
            "address": "123 Test St",
        }
        form = PropertyForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 6)


class PropertyViewsTest(TestCase):
    """Tests for the property views"""

    def setUp(self):
        self.landlord = LandlordFactory.create()
        self.user = self.landlord.user
        self.property = PropertyFactory.create(landlord=self.landlord)
        # self.client = Client()
        # self.client.login(email=self.user.email, password="password123")
        self.client.force_login(self.user)

    def test_property_list_view(self):
        """Test the property_list view"""
        response = self.client.get(reverse("property_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "property_list.html")
        self.assertEqual(len(response.context["properties"]), 1)
        self.assertIsInstance(response.context["form"], PropertyForm)

    def test_property_detail_view_get(self):
        """Test the property_detail view GET request"""
        response = self.client.get(reverse("property_detail", args=[self.property.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "property_detail.html")
        self.assertEqual(response.context["property"], self.property)
        self.assertIsInstance(response.context["form"], PropertyForm)

    def test_property_detail_view_post(self):
        """Test the property_detail view POST request"""
        updated_property = PropertyFactory.build(status=Property.StatusChoices.RENTED)

        form_data = {
            "address": updated_property.address,
            "city": updated_property.city,
            "postal_code": updated_property.postal_code,
            "area_m2": updated_property.area_m2,
            "current_rent": updated_property.current_rent,
            "additional_costs": updated_property.additional_costs,
            "status": updated_property.status,
        }
        response = self.client.post(
            reverse("property_detail", args=[self.property.id]), data=form_data
        )
        self.assertEqual(response.status_code, 302)
        self.property.refresh_from_db()
        self.assertEqual(self.property.address, updated_property.address)
        self.assertEqual(self.property.city, updated_property.city)
        self.assertEqual(self.property.status, Property.StatusChoices.RENTED)

    def test_property_create_view_get(self):
        """Test the PropertyCreateView GET request"""
        response = self.client.get(reverse("add_property"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "add_property.html")
        self.assertIsInstance(response.context["form"], PropertyForm)

    def test_property_create_view_post(self):
        """Test the PropertyCreateView POST request"""
        new_property_data = PropertyFactory.build()

        form_data = {
            "address": new_property_data.address,
            "city": new_property_data.city,
            "postal_code": new_property_data.postal_code,
            "area_m2": new_property_data.area_m2,
            "current_rent": new_property_data.current_rent,
            "additional_costs": new_property_data.additional_costs,
            "status": new_property_data.status,
        }
        response = self.client.post(reverse("add_property"), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Property.objects.count(), 2)

        new_property = Property.objects.latest("id")
        self.assertEqual(new_property.address, new_property_data.address)
        self.assertEqual(new_property.city, new_property_data.city)
        self.assertEqual(new_property.landlord, self.landlord)

    def test_property_update_view(self):
        """Test the PropertyUpdateView"""
        edited_property = PropertyFactory.build(
            status=Property.StatusChoices.MAINTENANCE
        )

        form_data = {
            "address": edited_property.address,
            "city": edited_property.city,
            "postal_code": edited_property.postal_code,
            "area_m2": edited_property.area_m2,
            "current_rent": edited_property.current_rent,
            "additional_costs": edited_property.additional_costs,
            "status": edited_property.status,
        }
        response = self.client.post(
            reverse("edit_property", args=[self.property.id]), data=form_data
        )
        self.assertEqual(response.status_code, 302)
        self.property.refresh_from_db()
        self.assertEqual(self.property.address, edited_property.address)
        self.assertEqual(self.property.city, edited_property.city)
        self.assertEqual(self.property.status, Property.StatusChoices.MAINTENANCE)

    def test_property_delete_view(self):
        """Test the PropertyDeleteView"""
        response = self.client.post(reverse("delete_property", args=[self.property.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Property.objects.count(), 0)
