from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid
from datetime import timedelta
from .models import Reminder, TenantInvitation
from .forms import ReminderForm, TenantInvitationForm
from properties.models import Property
from users.models import Landlord
from users.factories import LandlordFactory, CustomUserFactory
from properties.factories import PropertyFactory
from notifications.factories import ReminderFactory, TenantInvitationFactory

User = get_user_model()


class ReminderModelTest(TestCase):
    """Tests for the Reminder model"""

    def setUp(self):
        self.landlord = LandlordFactory.create()
        self.user = self.landlord.user
        self.property = PropertyFactory.create(landlord=self.landlord)
        self.reminder = ReminderFactory.create(property=self.property)

    def test_reminder_creation(self):
        """Test that a reminder can be created with all required fields"""
        self.assertIsNotNone(self.reminder.title)
        self.assertIsNotNone(self.reminder.description)
        self.assertTrue(self.reminder.due_date > timezone.now())
        self.assertEqual(self.reminder.property, self.property)

    def test_reminder_string_representation(self):
        """Test the string representation of a reminder"""
        self.assertEqual(str(self.reminder), self.reminder.title)


class TenantInvitationModelTest(TestCase):
    """Tests for the TenantInvitation model"""

    def setUp(self):
        self.landlord = LandlordFactory.create()
        self.user = self.landlord.user
        self.property = PropertyFactory.create(landlord=self.landlord)
        self.invitation = TenantInvitationFactory.create(
            property_unit=self.property, landlord=self.user
        )

    def test_invitation_creation(self):
        """Test that an invitation can be created with all required fields"""
        self.assertIsNotNone(self.invitation.email)
        self.assertEqual(self.invitation.property_unit, self.property)
        self.assertEqual(self.invitation.landlord, self.user)
        self.assertEqual(self.invitation.status, TenantInvitation.StatusChoices.PENDING)
        self.assertTrue(isinstance(self.invitation.token, uuid.UUID))

    def test_invitation_string_representation(self):
        """Test the string representation of an invitation"""
        expected_str = (
            f"Zaproszenie dla {self.invitation.email} - {self.invitation.property_unit}"
        )
        self.assertEqual(str(self.invitation), expected_str)

    def test_is_expired_property(self):
        """Test the is_expired property"""
        self.assertFalse(self.invitation.is_expired)
        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()
        self.assertTrue(self.invitation.is_expired)

    def test_is_pending_property(self):
        """Test the is_pending property"""
        self.assertTrue(self.invitation.is_pending)
        self.invitation.status = TenantInvitation.StatusChoices.ACCEPTED
        self.invitation.save()
        self.assertFalse(self.invitation.is_pending)


class ReminderFormTest(TestCase):
    """Tests for the ReminderForm"""

    def setUp(self):
        self.landlord = LandlordFactory.create()
        self.user = self.landlord.user
        self.property = PropertyFactory.create(landlord=self.landlord)

    def test_valid_form(self):
        """Test that the form is valid with all required fields"""
        reminder = ReminderFactory.build(property=self.property)

        form_data = {
            "title": reminder.title,
            "description": reminder.description,
            "due_date": reminder.due_date,
            "property": self.property.id,
        }
        form = ReminderForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self):
        """Test that the form is invalid when required fields are missing"""
        form_data = {
            "title": "Test Reminder",
        }
        form = ReminderForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 3)


class TenantInvitationFormTest(TestCase):
    """Tests for the TenantInvitationForm"""

    def setUp(self):
        self.landlord = LandlordFactory.create()
        self.user = self.landlord.user
        self.property = PropertyFactory.create(landlord=self.landlord)

    def test_valid_form(self):
        """Test that the form is valid with all required fields"""
        invitation = TenantInvitationFactory.build(
            property_unit=self.property, landlord=self.user
        )

        form_data = {"email": invitation.email, "property_unit": self.property.id}
        form = TenantInvitationForm(data=form_data, landlord=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self):
        """Test that the form is invalid when required fields are missing"""
        form_data = {}
        form = TenantInvitationForm(data=form_data, landlord=self.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)

    def test_property_filtering(self):
        """Test that properties are filtered by landlord"""
        other_user = User.objects.create_user(
            email="other@test.com",
            password="testpassword",
            role=User.RoleChoices.LANDLORD,
        )
        other_landlord = Landlord.objects.create(user=other_user)
        other_property = Property.objects.create(
            address="456 Other St",
            city="Other City",
            postal_code="67890",
            area_m2=200.0,
            current_rent=2000.0,
            additional_costs=300.0,
            status=Property.StatusChoices.AVAILABLE,
            landlord=other_landlord,
        )

        form = TenantInvitationForm(landlord=self.user)
        self.assertEqual(form.fields["property_unit"].queryset.count(), 1)
        self.assertIn(self.property, form.fields["property_unit"].queryset)
        self.assertNotIn(other_property, form.fields["property_unit"].queryset)


class ReminderViewsTest(TestCase):
    """Tests for the reminder views"""

    def setUp(self):
        self.landlord = LandlordFactory.create()
        self.user = self.landlord.user
        self.property = PropertyFactory.create(landlord=self.landlord)
        self.reminder = ReminderFactory.create(property=self.property)
        self.client = Client()
        self.client.login(email=self.user.email, password="password123")

    def test_add_reminder_view_get(self):
        """Test the add_reminder view GET request"""
        response = self.client.get(reverse("add_reminder"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "add_reminder.html")
        self.assertIsInstance(response.context["form"], ReminderForm)

    def test_add_reminder_view_post(self):
        """Test the add_reminder view POST request"""
        new_reminder_data = ReminderFactory.build(property=self.property)

        form_data = {
            "title": new_reminder_data.title,
            "description": new_reminder_data.description,
            "due_date": new_reminder_data.due_date.strftime("%Y-%m-%d"),
            "property": self.property.id,
        }
        response = self.client.post(reverse("add_reminder"), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reminder.objects.count(), 2)

        new_reminder = Reminder.objects.latest("id")
        self.assertEqual(new_reminder.title, new_reminder_data.title)
        self.assertEqual(new_reminder.description, new_reminder_data.description)

    def test_edit_reminder_view_get(self):
        """Test the edit_reminder view GET request"""
        response = self.client.get(reverse("edit_reminder", args=[self.reminder.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_reminder.html")
        self.assertIsInstance(response.context["form"], ReminderForm)
        self.assertEqual(response.context["reminder"], self.reminder)

    def test_edit_reminder_view_post(self):
        """Test the edit_reminder view POST request"""
        updated_reminder_data = ReminderFactory.build(property=self.property)

        form_data = {
            "title": updated_reminder_data.title,
            "description": updated_reminder_data.description,
            "due_date": updated_reminder_data.due_date.strftime("%Y-%m-%d"),
            "property": self.property.id,
        }
        response = self.client.post(
            reverse("edit_reminder", args=[self.reminder.id]), data=form_data
        )
        self.assertEqual(response.status_code, 302)
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.title, updated_reminder_data.title)
        self.assertEqual(self.reminder.description, updated_reminder_data.description)

    def test_delete_reminder_view(self):
        """Test the delete_reminder view"""
        response = self.client.post(reverse("delete_reminder", args=[self.reminder.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reminder.objects.count(), 0)


class TenantInvitationViewsTest(TestCase):
    """Tests for the tenant invitation views"""

    def setUp(self):
        self.landlord = LandlordFactory.create()
        self.user = self.landlord.user
        self.property = PropertyFactory.create(landlord=self.landlord)
        self.tenant_user = CustomUserFactory.create(role=User.RoleChoices.TENANT)
        self.invitation = TenantInvitationFactory.create(
            email=self.tenant_user.email,
            property_unit=self.property,
            landlord=self.user,
        )
        self.client = Client()
        self.client.login(email=self.user.email, password="password123")

    def test_send_invitation_view_get(self):
        """Test the send_invitation view GET request"""
        response = self.client.get(reverse("send_invitation"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "send_invitation.html")
        self.assertIsInstance(response.context["form"], TenantInvitationForm)

    def test_send_invitation_view_post(self):
        """Test the send_invitation view POST request"""
        new_tenant = CustomUserFactory.build(role=User.RoleChoices.TENANT)

        form_data = {"email": new_tenant.email, "property_unit": self.property.id}
        response = self.client.post(reverse("send_invitation"), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TenantInvitation.objects.count(), 2)

        new_invitation = TenantInvitation.objects.get(email=new_tenant.email)
        self.assertEqual(new_invitation.property_unit, self.property)

    def test_accept_invitation_view(self):
        """Test the accept_invitation view"""
        self.client.logout()
        self.client.login(email=self.tenant_user.email, password="password123")

        response = self.client.get(
            reverse("accept_invitation", args=[self.invitation.token])
        )
        self.assertEqual(response.status_code, 200)

        new_password = f"password_{uuid.uuid4().hex[:8]}"

        form_data = {"password": new_password, "password_confirm": new_password}
        response = self.client.post(
            reverse("accept_invitation", args=[self.invitation.token]), data=form_data
        )
        self.assertEqual(response.status_code, 302)

        self.invitation.refresh_from_db()
        self.assertEqual(
            self.invitation.status, TenantInvitation.StatusChoices.ACCEPTED
        )
