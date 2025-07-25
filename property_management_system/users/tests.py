from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import CustomUser
from .forms import CustomUserCreationForm
from .factories import CustomUserFactory

User = get_user_model()


class UsersManagersTests(TestCase):
    """Tests for the custom user manager"""

    def test_create_user(self):
        """Test creating a regular user with the custom user manager"""
        test_user = CustomUserFactory.build()
        email = test_user.email
        password = "test_password"

        user = User.objects.create_user(email=email, password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        try:
            self.assertIsNone(user.username)
        except AttributeError:
            pass
        with self.assertRaises(TypeError):
            User.objects.create_user()
        with self.assertRaises(TypeError):
            User.objects.create_user(email="")
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password=password)

    def test_create_superuser(self):
        """Test creating a superuser with the custom user manager"""
        test_user = CustomUserFactory.build()
        email = test_user.email
        password = "admin_password"

        admin_user = User.objects.create_superuser(email=email, password=password)
        self.assertEqual(admin_user.email, email)
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        try:
            self.assertIsNone(admin_user.username)
        except AttributeError:
            pass
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email=email, password=password, is_superuser=False
            )


class AuthenticationTests(TestCase):
    """Tests for user authentication functionality"""

    def setUp(self):
        self.client = Client()
        self.test_user = CustomUserFactory.create(email="testuser@example.com")
        self.login_url = reverse("login")
        self.register_url = reverse("register")
        self.dashboard_url = reverse("dashboard")

    def test_user_registration_get(self):
        """Test GET request to registration page loads correctly"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sign-up.html")
        self.assertIsInstance(response.context["form"], CustomUserCreationForm)

    def test_user_registration_post_valid(self):
        """Test valid user registration"""
        user_count = User.objects.count()
        test_user = CustomUserFactory.build()
        password = "complex_password123"

        data = {
            "email": test_user.email,
            "password1": password,
            "password2": password,
        }

        response = self.client.post(self.register_url, data)
        self.assertRedirects(response, self.dashboard_url)
        self.assertEqual(User.objects.count(), user_count + 1)
        new_user = User.objects.get(email=test_user.email)
        self.assertEqual(new_user.role, CustomUser.RoleChoices.TENANT)

    def test_user_registration_post_invalid(self):
        """Test invalid user registration (passwords don't match)"""
        user_count = User.objects.count()
        test_user = CustomUserFactory.build()

        data = {
            "email": test_user.email,
            "password1": "complex_password123",
            "password2": "different_password",
        }

        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(User.objects.count(), user_count)

    def test_user_login_get(self):
        """Test GET request to login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sign-in.html")

    def test_user_login_post_valid(self):
        """Test valid user login"""
        data = {
            "username": "testuser@example.com",
            "password": "password123",
        }

        response = self.client.post(self.login_url, data)
        self.assertRedirects(response, self.dashboard_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_user_login_post_invalid(self):
        """Test invalid user login"""
        data = {
            "username": "testuser@example.com",
            "password": "wrong_password",
        }

        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_user_logout(self):
        """Test that a user can successfully log out"""
        self.client.login(username="testuser@example.com", password="password123")
        self.assertTrue(self.client.session.get("_auth_user_id"))

        logout_url = reverse("logout")
        response = self.client.post(logout_url)
        self.assertRedirects(response, self.login_url)
        self.assertFalse("_auth_user_id" in self.client.session)

    def test_logout_redirect(self):
        """Test that logout redirects to the correct page"""
        self.client.login(username="testuser@example.com", password="password123")
        logout_url = reverse("logout")
        self.client.login(username="testuser@example.com", password="password123")
        response = self.client.post(logout_url)
        self.assertRedirects(response, self.login_url)


class UserRoleTests(TestCase):
    """Tests for user role functionality"""

    def setUp(self):
        self.client = Client()
        self.tenant_user = CustomUserFactory.create(
            email="tenant@example.com", role=CustomUser.RoleChoices.TENANT
        )
        self.landlord_user = CustomUserFactory.create(
            email="landlord@example.com", role=CustomUser.RoleChoices.LANDLORD
        )
        self.admin_user = CustomUserFactory.create(
            email="admin@example.com", role=CustomUser.RoleChoices.ADMINISTRATOR
        )

    def test_default_role(self):
        """Test that new users get the default TENANT role"""
        new_user = CustomUserFactory.create(
            email="newuser@example.com",
        )
        self.assertEqual(new_user.role, CustomUser.RoleChoices.TENANT)

    def test_set_role(self):
        """Test setting a user's role"""
        user = CustomUserFactory.create(email="roletest@example.com")
        self.assertEqual(user.role, CustomUser.RoleChoices.TENANT)

        user.role = CustomUser.RoleChoices.LANDLORD
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.role, CustomUser.RoleChoices.LANDLORD)

        user.role = CustomUser.RoleChoices.ADMINISTRATOR
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.role, CustomUser.RoleChoices.ADMINISTRATOR)
