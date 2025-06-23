from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import CustomUser
from .forms import CustomUserCreationForm

User = get_user_model()

class UsersManagersTests(TestCase):

    def test_create_user(self):
        user = User.objects.create_user(email="normal@user.com", password="foo")
        self.assertEqual(user.email, "normal@user.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(user.username)
        except AttributeError:
            pass
        with self.assertRaises(TypeError):
            User.objects.create_user()
        with self.assertRaises(TypeError):
            User.objects.create_user(email="")
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="foo")

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(email="super@user.com", password="foo")
        self.assertEqual(admin_user.email, "super@user.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(admin_user.username)
        except AttributeError:
            pass
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="super@user.com", password="foo", is_superuser=False)


class AuthenticationTests(TestCase):
    def setUp(self):
        # Create a test client
        self.client = Client()

        # Create a test user
        self.test_user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123'
        )

        # URLs
        self.login_url = reverse('login')
        self.register_url = reverse('register')
        self.dashboard_url = reverse('dashboard')

    def test_user_registration_get(self):
        """Test GET request to registration page loads correctly"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign-up.html')
        self.assertIsInstance(response.context['form'], CustomUserCreationForm)

    def test_user_registration_post_valid(self):
        """Test valid user registration"""
        user_count = User.objects.count()

        # Registration data
        data = {
            'email': 'newuser@example.com',
            'password1': 'complex_password123',
            'password2': 'complex_password123',
        }

        response = self.client.post(self.register_url, data)

        # Check redirect to dashboard
        self.assertRedirects(response, self.dashboard_url)

        # Check user was created
        self.assertEqual(User.objects.count(), user_count + 1)

        # Check the new user has the default role (TENANT)
        new_user = User.objects.get(email='newuser@example.com')
        self.assertEqual(new_user.role, CustomUser.RoleChoices.TENANT)

    def test_user_registration_post_invalid(self):
        """Test invalid user registration (passwords don't match)"""
        user_count = User.objects.count()

        # Invalid registration data
        data = {
            'email': 'newuser@example.com',
            'password1': 'complex_password123',
            'password2': 'different_password',
        }

        response = self.client.post(self.register_url, data)

        # Check form is invalid
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

        # Check user was not created
        self.assertEqual(User.objects.count(), user_count)

    def test_user_login_get(self):
        """Test GET request to login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign-in.html')

    def test_user_login_post_valid(self):
        """Test valid user login"""
        data = {
            'username': 'testuser@example.com',  # Django's LoginView uses 'username' for the field
            'password': 'testpassword123',
        }

        response = self.client.post(self.login_url, data)

        # Check redirect to dashboard
        self.assertRedirects(response, self.dashboard_url)

        # Check user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_user_login_post_invalid(self):
        """Test invalid user login"""
        data = {
            'username': 'testuser@example.com',
            'password': 'wrong_password',
        }

        response = self.client.post(self.login_url, data)

        # Check form is invalid
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class UserRoleTests(TestCase):
    def setUp(self):
        # Create a test client
        self.client = Client()

        # Create users with different roles
        self.tenant_user = User.objects.create_user(
            email='tenant@example.com',
            password='password123',
            role=CustomUser.RoleChoices.TENANT
        )

        self.landlord_user = User.objects.create_user(
            email='landlord@example.com',
            password='password123',
            role=CustomUser.RoleChoices.LANDLORD
        )

        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='password123',
            role=CustomUser.RoleChoices.ADMINISTRATOR
        )

    def test_default_role(self):
        """Test that new users get the default TENANT role"""
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='password123'
        )
        self.assertEqual(new_user.role, CustomUser.RoleChoices.TENANT)

    def test_set_role(self):
        """Test setting a user's role"""
        user = User.objects.create_user(
            email='roletest@example.com',
            password='password123'
        )

        # Initially a tenant
        self.assertEqual(user.role, CustomUser.RoleChoices.TENANT)

        # Change to landlord
        user.role = CustomUser.RoleChoices.LANDLORD
        user.save()

        # Refresh from database
        user.refresh_from_db()
        self.assertEqual(user.role, CustomUser.RoleChoices.LANDLORD)

        # Change to administrator
        user.role = CustomUser.RoleChoices.ADMINISTRATOR
        user.save()

        # Refresh from database
        user.refresh_from_db()
        self.assertEqual(user.role, CustomUser.RoleChoices.ADMINISTRATOR)