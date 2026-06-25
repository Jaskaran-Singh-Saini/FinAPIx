from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from watchlist.models import Watchlist


# ─────────────────────────────────────────────
# 1. Watchlist Model Tests
# ─────────────────────────────────────────────

class WatchlistModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="investor", password="pass123")

    def test_str_representation(self):
        w = Watchlist.objects.create(user=self.user, symbol="AAPL")
        self.assertEqual(str(w), "investor - AAPL")

    def test_symbol_stored_uppercase(self):
        # model stores whatever is passed — view enforces uppercase
        w = Watchlist.objects.create(user=self.user, symbol="AAPL")
        self.assertEqual(w.symbol, "AAPL")

    def test_unique_together_prevents_duplicates(self):
        from django.db import IntegrityError
        Watchlist.objects.create(user=self.user, symbol="TSLA")
        with self.assertRaises(IntegrityError):
            Watchlist.objects.create(user=self.user, symbol="TSLA")


# ─────────────────────────────────────────────
# 2. Add to Watchlist Tests
# ─────────────────────────────────────────────

class AddToWatchlistTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="investor", password="pass123")
        self.client.login(username="investor", password="pass123")

    def test_add_symbol_creates_watchlist_entry(self):
        self.client.post(reverse("add_to_watchlist", args=["AAPL"]))
        self.assertTrue(Watchlist.objects.filter(user=self.user, symbol="AAPL").exists())

    def test_add_symbol_is_case_insensitive(self):
        self.client.post(reverse("add_to_watchlist", args=["aapl"]))
        self.assertTrue(Watchlist.objects.filter(user=self.user, symbol="AAPL").exists())

    def test_add_duplicate_does_not_create_second_entry(self):
        self.client.post(reverse("add_to_watchlist", args=["AAPL"]))
        self.client.post(reverse("add_to_watchlist", args=["AAPL"]))
        self.assertEqual(Watchlist.objects.filter(user=self.user, symbol="AAPL").count(), 1)

    def test_add_ajax_returns_json_success(self):
        response = self.client.post(
            reverse("add_to_watchlist", args=["MSFT"]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["symbol"], "MSFT")

    def test_add_redirects_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(reverse("add_to_watchlist", args=["AAPL"]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Watchlist.objects.filter(symbol="AAPL").exists())


# ─────────────────────────────────────────────
# 3. Remove from Watchlist Tests
# ─────────────────────────────────────────────

class RemoveFromWatchlistTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="investor", password="pass123")
        self.client.login(username="investor", password="pass123")
        Watchlist.objects.create(user=self.user, symbol="NVDA")

    def test_remove_deletes_entry(self):
        self.client.post(reverse("remove_from_watchlist", args=["NVDA"]))
        self.assertFalse(Watchlist.objects.filter(user=self.user, symbol="NVDA").exists())

    def test_remove_ajax_returns_json_success(self):
        response = self.client.post(
            reverse("remove_from_watchlist", args=["NVDA"]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

    def test_remove_nonexistent_symbol_does_not_crash(self):
        response = self.client.post(reverse("remove_from_watchlist", args=["ZZZZ"]))
        self.assertEqual(response.status_code, 302)  # redirect, no error

    def test_remove_does_not_affect_other_users_watchlist(self):
        other = User.objects.create_user(username="other", password="pass123")
        Watchlist.objects.create(user=other, symbol="NVDA")
        self.client.post(reverse("remove_from_watchlist", args=["NVDA"]))
        self.assertTrue(Watchlist.objects.filter(user=other, symbol="NVDA").exists())


# ─────────────────────────────────────────────
# 4. Watchlist Page Tests
# ─────────────────────────────────────────────

class WatchlistPageTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="investor", password="pass123")
        self.client.login(username="investor", password="pass123")

    def test_watchlist_page_loads(self):
        response = self.client.get(reverse("watchlist_list"))
        self.assertEqual(response.status_code, 200)

    def test_watchlist_page_shows_symbols(self):
        Watchlist.objects.create(user=self.user, symbol="AAPL")
        Watchlist.objects.create(user=self.user, symbol="TSLA")
        response = self.client.get(reverse("watchlist_list"))
        self.assertContains(response, "AAPL")
        self.assertContains(response, "TSLA")

    def test_watchlist_page_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("watchlist_list"))
        self.assertEqual(response.status_code, 302)

    def test_watchlist_only_shows_current_users_symbols(self):
        other = User.objects.create_user(username="other", password="pass123")
        Watchlist.objects.create(user=other, symbol="GOOGL")
        Watchlist.objects.create(user=self.user, symbol="AAPL")
        response = self.client.get(reverse("watchlist_list"))
        self.assertContains(response, "AAPL")
        # GOOGL appears in the ticker tape, so check it's not in a watchlist table row
        self.assertNotContains(response, 'id="row-GOOGL"')