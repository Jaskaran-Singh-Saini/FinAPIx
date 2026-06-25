from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


# ─────────────────────────────────────────────
# 1. Registration Tests
# ─────────────────────────────────────────────

class RegisterViewTest(TestCase):

    def test_register_page_loads(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

    def test_successful_registration_creates_user(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_successful_registration_logs_user_in(self):
        self.client.post(reverse("register"), {
            "username": "newuser",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        response = self.client.get(reverse("stock_dashboard"))
        self.assertEqual(response.status_code, 200)  # not redirected to login

    def test_successful_registration_redirects_to_dashboard(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertRedirects(response, reverse("stock_dashboard"))

    def test_registration_fails_on_password_mismatch(self):
        self.client.post(reverse("register"), {
            "username": "baduser",
            "password1": "StrongPass123!",
            "password2": "WrongPass456!",
        })
        self.assertFalse(User.objects.filter(username="baduser").exists())

    def test_registration_fails_on_duplicate_username(self):
        User.objects.create_user(username="existing", password="pass123")
        response = self.client.post(reverse("register"), {
            "username": "existing",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertEqual(User.objects.filter(username="existing").count(), 1)

    def test_authenticated_user_redirected_away_from_register(self):
        User.objects.create_user(username="user1", password="pass123")
        self.client.login(username="user1", password="pass123")
        response = self.client.get(reverse("register"))
        self.assertRedirects(response, reverse("stock_dashboard"))


# ─────────────────────────────────────────────
# 2. Login Tests
# ─────────────────────────────────────────────

class LoginViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass1234!")

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_successful_login_redirects_to_dashboard(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "pass1234!",
        })
        self.assertRedirects(response, reverse("stock_dashboard"))

    def test_wrong_password_stays_on_login(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_nonexistent_user_stays_on_login(self):
        response = self.client.post(reverse("login"), {
            "username": "ghost",
            "password": "pass1234!",
        })
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_redirected_away_from_login(self):
        self.client.login(username="testuser", password="pass1234!")
        response = self.client.get(reverse("login"))
        self.assertRedirects(response, reverse("stock_dashboard"))


# ─────────────────────────────────────────────
# 3. Logout Tests
# ─────────────────────────────────────────────

class LogoutViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass1234!")
        self.client.login(username="testuser", password="pass1234!")

    def test_logout_redirects_to_login(self):
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))

    def test_user_is_logged_out_after_logout(self):
        self.client.post(reverse("logout"))
        # stock_dashboard is public; check a login-required page instead
        response = self.client.get(reverse("watchlist_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])