from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch
from datetime import date
from stocks.models import StockIndicator


# ─────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────

def make_indicator(symbol="AAPL", d=date(2024, 1, 15), close=185.0,
                   rsi=55.0, sma_14=180.0, macd_line=1.5,
                   bb_upper=195.0, bb_lower=175.0):
    return StockIndicator.objects.create(
        symbol=symbol, date=d, close=close,
        rsi=rsi, sma_14=sma_14, macd_line=macd_line,
        bb_upper=bb_upper, bb_lower=bb_lower,
    )


# ─────────────────────────────────────────────
# 1. Dashboard View Tests
# ─────────────────────────────────────────────

class DashboardViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="trader", password="pass123")
        self.client.login(username="trader", password="pass123")

    def test_dashboard_loads_with_existing_data(self):
        make_indicator()
        response = self.client.get(reverse("stock_dashboard") + "?symbol=AAPL")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_defaults_to_aapl(self):
        make_indicator()
        response = self.client.get(reverse("stock_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["symbol"], "AAPL")

    def test_dashboard_passes_symbol_to_context(self):
        make_indicator(symbol="TSLA")
        response = self.client.get(reverse("stock_dashboard") + "?symbol=TSLA")
        self.assertEqual(response.context["symbol"], "TSLA")

    def test_dashboard_uppercase_normalises_symbol(self):
        make_indicator(symbol="MSFT")
        response = self.client.get(reverse("stock_dashboard") + "?symbol=msft")
        self.assertEqual(response.context["symbol"], "MSFT")

    def test_dashboard_accessible_without_login(self):
        """Dashboard should be public (no @login_required on stock_dashboard)."""
        self.client.logout()
        make_indicator()
        response = self.client.get(reverse("stock_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_shows_error_for_unknown_symbol(self):
        """No data + fetch fails → error in context."""
        with patch("dashboard.views.fetch_and_save_stock_data", return_value=None):
            response = self.client.get(reverse("stock_dashboard") + "?symbol=ZZZZ")
        self.assertIn("error", response.context)

    def test_dashboard_date_filter_narrows_data(self):
        make_indicator(d=date(2024, 1, 10))
        make_indicator(symbol="AAPL", d=date(2024, 1, 20), close=190.0)
        response = self.client.get(
            reverse("stock_dashboard") + "?symbol=AAPL&start=2024-01-18&end=2024-01-22"
        )
        self.assertEqual(response.status_code, 200)

    def test_dashboard_shows_error_for_empty_date_range(self):
        make_indicator(d=date(2024, 1, 10))
        response = self.client.get(
            reverse("stock_dashboard") + "?symbol=AAPL&start=2023-01-01&end=2023-01-31"
        )
        self.assertIn("error", response.context)


# ─────────────────────────────────────────────
# 2. Chart Data Tests
# ─────────────────────────────────────────────

class BuildChartDataTest(TestCase):

    def test_chart_data_json_in_response(self):
        make_indicator()
        response = self.client.get(reverse("stock_dashboard") + "?symbol=AAPL")
        self.assertIn("chart_data", response.context)
        import json
        data = json.loads(response.context["chart_data"])
        self.assertIn("labels", data)
        self.assertIn("closes", data)
        self.assertIn("rsi", data)
        self.assertIn("macd", data)

    def test_chart_data_has_correct_length(self):
        for i in range(3):
            StockIndicator.objects.create(
                symbol="AAPL",
                date=date(2024, 1, 10 + i),
                close=180.0 + i,
                rsi=55.0, sma_14=179.0, macd_line=1.0,
                bb_upper=190.0, bb_lower=170.0,
            )
        import json
        response = self.client.get(reverse("stock_dashboard") + "?symbol=AAPL")
        data = json.loads(response.context["chart_data"])
        self.assertEqual(len(data["labels"]), 3)
        self.assertEqual(len(data["closes"]), 3)

    def test_chart_data_handles_nan_indicators(self):
        """NaN floats must be serialised as null, not raise JSON error."""
        import math
        StockIndicator.objects.create(
            symbol="AAPL", date=date(2024, 1, 5),
            close=180.0, rsi=float("nan"),
        )
        import json
        response = self.client.get(reverse("stock_dashboard") + "?symbol=AAPL")
        # Should not raise — chart_data must be valid JSON
        data = json.loads(response.context["chart_data"])
        self.assertIsNone(data["rsi"][0])


# ─────────────────────────────────────────────
# 3. ML Prediction Integration Tests
# ─────────────────────────────────────────────

class DashboardMLPredictionTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="trader", password="pass123")
        self.client.login(username="trader", password="pass123")
        make_indicator()

    def test_prediction_context_present(self):
        from unittest.mock import MagicMock
        mock_model = MagicMock()
        mock_model.predict.return_value = [1]
        mock_model.predict_proba.return_value = [[0.25, 0.75]]

        with patch("stocks.ml_predict.load_model", return_value=mock_model):
            response = self.client.get(reverse("stock_dashboard") + "?symbol=AAPL")

        self.assertIn("prediction", response.context)
        pred = response.context["prediction"]
        self.assertTrue(pred["model_loaded"])

    def test_prediction_shown_when_model_missing(self):
        with patch("stocks.ml_predict.load_model", return_value=None):
            response = self.client.get(reverse("stock_dashboard") + "?symbol=AAPL")
        pred = response.context["prediction"]
        self.assertFalse(pred["model_loaded"])