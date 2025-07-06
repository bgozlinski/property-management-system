from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid
from datetime import timedelta

from .models import Reminder, TenantInvitation
from .forms import ReminderForm, TenantInvitationForm
from properties.models import Property
from users.models import Landlord

User = get_user_model()


class ReminderModelTest(TestCase):
    """Tests for the Reminder model"""

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

        # Create a test reminder
        self.reminder = Reminder.objects.create(
            title='Test Reminder',
            description='This is a test reminder',
            due_date=timezone.now() + timedelta(days=7),
            property=self.property
        )

    def test_reminder_creation(self):
        """Test that a reminder can be created with all required fields"""
        self.assertEqual(self.reminder.title, 'Test Reminder')
        self.assertEqual(self.reminder.description, 'This is a test reminder')
        self.assertTrue(self.reminder.due_date > timezone.now())
        self.assertEqual(self.reminder.property, self.property)

    def test_reminder_string_representation(self):
        """Test the string representation of a reminder"""
        self.assertEqual(str(self.reminder), 'Test Reminder')


class TenantInvitationModelTest(TestCase):
    """Tests for the TenantInvitation model"""

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

        # Create a test invitation
        self.invitation = TenantInvitation.objects.create(
            email='tenant@test.com',
            property_unit=self.property,
            landlord=self.user,
            expires_at=timezone.now() + timedelta(days=7)
        )

    def test_invitation_creation(self):
        """Test that an invitation can be created with all required fields"""
        self.assertEqual(self.invitation.email, 'tenant@test.com')
        self.assertEqual(self.invitation.property_unit, self.property)
        self.assertEqual(self.invitation.landlord, self.user)
        self.assertEqual(self.invitation.status, TenantInvitation.StatusChoices.PENDING)
        self.assertTrue(isinstance(self.invitation.token, uuid.UUID))

    def test_invitation_string_representation(self):
        """Test the string representation of an invitation"""
        expected_str = f"Zaproszenie dla {self.invitation.email} - {self.invitation.property_unit}"
        self.assertEqual(str(self.invitation), expected_str)

    def test_is_expired_property(self):
        """Test the is_expired property"""
        # Not expired
        self.assertFalse(self.invitation.is_expired)

        # Set to expired
        self.invitation.expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()
        self.assertTrue(self.invitation.is_expired)

    def test_is_pending_property(self):
        """Test the is_pending property"""
        # Initially pending
        self.assertTrue(self.invitation.is_pending)

        # Change status
        self.invitation.status = TenantInvitation.StatusChoices.ACCEPTED
        self.invitation.save()
        self.assertFalse(self.invitation.is_pending)


class ReminderFormTest(TestCase):
    """Tests for the ReminderForm"""

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

    def test_valid_form(self):
        """Test that the form is valid with all required fields"""
        form_data = {
            'title': 'Test Reminder',
            'description': 'This is a test reminder',
            'due_date': timezone.now() + timedelta(days=7),
            'property': self.property.id
        }
        form = ReminderForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self):
        """Test that the form is invalid when required fields are missing"""
        form_data = {
            'title': 'Test Reminder',
            # Missing description, due_date, and property
        }
        form = ReminderForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 3)


class TenantInvitationFormTest(TestCase):
    """Tests for the TenantInvitationForm"""

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

    def test_valid_form(self):
        """Test that the form is valid with all required fields"""
        form_data = {
            'email': 'tenant@test.com',
            'property_unit': self.property.id
        }
        form = TenantInvitationForm(data=form_data, landlord=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self):
        """Test that the form is invalid when required fields are missing"""
        form_data = {
            # Missing email and property_unit
        }
        form = TenantInvitationForm(data=form_data, landlord=self.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)

    def test_property_filtering(self):
        """Test that properties are filtered by landlord"""
        # Create another landlord and property
        other_user = User.objects.create_user(
            email='other@test.com',
            password='testpassword',
            role=User.RoleChoices.LANDLORD
        )
        other_landlord = Landlord.objects.create(user=other_user)
        other_property = Property.objects.create(
            address='456 Other St',
            city='Other City',
            postal_code='67890',
            area_m2=200.0,
            current_rent=2000.0,
            additional_costs=300.0,
            status=Property.StatusChoices.AVAILABLE,
            landlord=other_landlord
        )

        # Check that form for first landlord only shows their properties
        form = TenantInvitationForm(landlord=self.user)
        self.assertEqual(form.fields['property_unit'].queryset.count(), 1)
        self.assertIn(self.property, form.fields['property_unit'].queryset)
        self.assertNotIn(other_property, form.fields['property_unit'].queryset)


class ReminderViewsTest(TestCase):
    """Tests for the reminder views"""

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

        # Create a test reminder
        self.reminder = Reminder.objects.create(
            title='Test Reminder',
            description='This is a test reminder',
            due_date=timezone.now() + timedelta(days=7),
            property=self.property
        )

        # Set up the client
        self.client = Client()
        self.client.login(email='landlord@test.com', password='testpassword')

    def test_add_reminder_view_get(self):
        """Test the add_reminder view GET request"""
        response = self.client.get(reverse('add_reminder'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'add_reminder.html')
        self.assertIsInstance(response.context['form'], ReminderForm)

    def test_add_reminder_view_post(self):
        """Test the add_reminder view POST request"""
        form_data = {
            'title': 'New Reminder',
            'description': 'This is a new reminder',
            'due_date': (timezone.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
            'property': self.property.id
        }
        response = self.client.post(reverse('add_reminder'), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Reminder.objects.count(), 2)
        new_reminder = Reminder.objects.get(title='New Reminder')
        self.assertEqual(new_reminder.description, 'This is a new reminder')

    def test_edit_reminder_view_get(self):
        """Test the edit_reminder view GET request"""
        response = self.client.get(reverse('edit_reminder', args=[self.reminder.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_reminder.html')
        self.assertIsInstance(response.context['form'], ReminderForm)
        self.assertEqual(response.context['reminder'], self.reminder)

    def test_edit_reminder_view_post(self):
        """Test the edit_reminder view POST request"""
        form_data = {
            'title': 'Updated Reminder',
            'description': 'This reminder has been updated',
            'due_date': (timezone.now() + timedelta(days=21)).strftime('%Y-%m-%d'),
            'property': self.property.id
        }
        response = self.client.post(reverse('edit_reminder', args=[self.reminder.id]), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.title, 'Updated Reminder')
        self.assertEqual(self.reminder.description, 'This reminder has been updated')

    def test_delete_reminder_view(self):
        """Test the delete_reminder view"""
        response = self.client.post(reverse('delete_reminder', args=[self.reminder.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        self.assertEqual(Reminder.objects.count(), 0)


class TenantInvitationViewsTest(TestCase):
    """Tests for the tenant invitation views"""

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

        # Create a test tenant user
        self.tenant_user = User.objects.create_user(
            email='tenant@test.com',
            password='testpassword',
            role=User.RoleChoices.TENANT
        )

        # Create a test invitation
        self.invitation = TenantInvitation.objects.create(
            email='tenant@test.com',
            property_unit=self.property,
            landlord=self.user,
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Set up the client
        self.client = Client()
        self.client.login(email='landlord@test.com', password='testpassword')

    def test_send_invitation_view_get(self):
        """Test the send_invitation view GET request"""
        response = self.client.get(reverse('send_invitation'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'send_invitation.html')  # Assuming this template exists
        self.assertIsInstance(response.context['form'], TenantInvitationForm)

    def test_send_invitation_view_post(self):
        """Test the send_invitation view POST request"""
        form_data = {
            'email': 'newtenant@test.com',
            'property_unit': self.property.id
        }
        response = self.client.post(reverse('send_invitation'), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(TenantInvitation.objects.count(), 2)
        new_invitation = TenantInvitation.objects.get(email='newtenant@test.com')
        self.assertEqual(new_invitation.property_unit, self.property)

    def test_accept_invitation_view(self):
        """Test the accept_invitation view"""
        # Log in as tenant
        self.client.logout()
        self.client.login(email='tenant@test.com', password='testpassword')

        # Access the accept invitation view
        response = self.client.get(reverse('accept_invitation', args=[self.invitation.token]))
        self.assertEqual(response.status_code, 302)  # Redirect after successful acceptance

        # Check that invitation status is updated
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, TenantInvitation.StatusChoices.ACCEPTED)


class ReminderAPITest(TestCase):
    """Tests for the Reminder API views"""

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

        # Create a test reminder
        self.reminder = Reminder.objects.create(
            title='Test Reminder',
            description='This is a test reminder',
            due_date=timezone.now() + timedelta(days=7),
            property=self.property
        )

        # Set up the API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_reminders(self):
        """Test listing reminders via API"""
        response = self.client.get(reverse('api_reminder_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Reminder')

    def test_create_reminder(self):
        """Test creating a reminder via API"""
        data = {
            'title': 'API Reminder',
            'description': 'Created via API',
            'due_date': (timezone.now() + timedelta(days=10)).isoformat(),
            'property': self.property.id
        }
        response = self.client.post(reverse('api_reminder_list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reminder.objects.count(), 2)
        new_reminder = Reminder.objects.get(title='API Reminder')
        self.assertEqual(new_reminder.description, 'Created via API')

    def test_retrieve_reminder(self):
        """Test retrieving a single reminder via API"""
        response = self.client.get(reverse('api_reminder_detail', args=[self.reminder.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Reminder')

    def test_update_reminder(self):
        """Test updating a reminder via API"""
        data = {
            'title': 'Updated API Reminder',
            'description': 'Updated via API',
            'due_date': (timezone.now() + timedelta(days=15)).isoformat(),
            'property': self.property.id
        }
        response = self.client.put(reverse('api_reminder_detail', args=[self.reminder.id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.title, 'Updated API Reminder')
        self.assertEqual(self.reminder.description, 'Updated via API')

    def test_delete_reminder(self):
        """Test deleting a reminder via API"""
        response = self.client.delete(reverse('api_reminder_detail', args=[self.reminder.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Reminder.objects.count(), 0)