from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from datetime import date
from stocks.models import StockIndicator, TrackedStock
from stocks.ml_predict import predict_trend


# ─────────────────────────────────────────────
# 1. Model Tests
# ─────────────────────────────────────────────

class StockIndicatorModelTest(TestCase):

    def setUp(self):
        self.entry = StockIndicator.objects.create(
            symbol="AAPL",
            date=date(2024, 1, 15),
            close=185.5,
            rsi=58.3,
            sma_14=182.0,
            macd_line=1.2,
            bb_upper=190.0,
            bb_lower=175.0,
        )

    def test_str_representation(self):
        self.assertEqual(str(self.entry), "AAPL - 2024-01-15")

    def test_fields_saved_correctly(self):
        obj = StockIndicator.objects.get(symbol="AAPL", date=date(2024, 1, 15))
        self.assertEqual(obj.close, 185.5)
        self.assertEqual(obj.rsi, 58.3)
        self.assertEqual(obj.sma_14, 182.0)

    def test_unique_together_constraint(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            StockIndicator.objects.create(
                symbol="AAPL",
                date=date(2024, 1, 15),
                close=190.0,
            )

    def test_nullable_indicators(self):
        entry = StockIndicator.objects.create(
            symbol="TSLA",
            date=date(2024, 1, 1),
            close=200.0,
        )
        self.assertIsNone(entry.rsi)
        self.assertIsNone(entry.sma_14)

    def test_default_ordering_is_descending(self):
        StockIndicator.objects.create(symbol="MSFT", date=date(2024, 1, 10), close=300.0)
        StockIndicator.objects.create(symbol="MSFT", date=date(2024, 1, 12), close=310.0)
        qs = StockIndicator.objects.filter(symbol="MSFT")
        self.assertEqual(qs.first().date, date(2024, 1, 12))


class TrackedStockModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="trader", password="pass123")

    def test_str_representation(self):
        ts = TrackedStock.objects.create(user=self.user, symbol="NVDA")
        self.assertEqual(str(ts), "trader - NVDA")

    def test_unique_together_constraint(self):
        from django.db import IntegrityError
        TrackedStock.objects.create(user=self.user, symbol="AAPL")
        with self.assertRaises(IntegrityError):
            TrackedStock.objects.create(user=self.user, symbol="AAPL")


# ─────────────────────────────────────────────
# 2. fetch_and_save_stock_data Tests
# ─────────────────────────────────────────────

class FetchAndSaveStockDataTest(TestCase):

    @patch("stocks.utils.yf.download")
    def test_returns_error_on_empty_dataframe(self, mock_download):
        import pandas as pd
        mock_download.return_value = pd.DataFrame()
        from stocks.utils import fetch_and_save_stock_data
        result = fetch_and_save_stock_data("FAKE")
        self.assertIn("No data", result)

    @patch("stocks.utils.yf.download")
    def test_saves_records_on_valid_data(self, mock_download):
        import pandas as pd
        import numpy as np
        from stocks.utils import fetch_and_save_stock_data

        dates = pd.date_range("2024-01-01", periods=30, freq="B")
        close_prices = np.linspace(150, 180, 30)
        df = pd.DataFrame({
            "Close": close_prices,
            "Open":  close_prices - 1,
            "High":  close_prices + 2,
            "Low":   close_prices - 2,
            "Volume": [1_000_000] * 30,
        }, index=dates)
        mock_download.return_value = df

        result = fetch_and_save_stock_data("AAPL")
        self.assertIn("AAPL", result)
        self.assertTrue(StockIndicator.objects.filter(symbol="AAPL").exists())

    @patch("stocks.utils.yf.download", side_effect=Exception("Network error"))
    def test_handles_exception_gracefully(self, mock_download):
        from stocks.utils import fetch_and_save_stock_data
        result = fetch_and_save_stock_data("AAPL")
        self.assertIn("Error", result)


# ─────────────────────────────────────────────
# 3. ML Prediction Tests
# ─────────────────────────────────────────────

class PredictTrendTest(TestCase):

    def test_returns_unknown_when_no_db_data(self):
        result = predict_trend("ZZZZ")
        self.assertEqual(result["signal"], "UNKNOWN")

    def test_returns_model_not_loaded_when_no_joblib(self):
        with patch("stocks.ml_predict.load_model", return_value=None):
            result = predict_trend("AAPL")
            self.assertFalse(result["model_loaded"])

    def test_returns_unknown_when_features_missing(self):
        StockIndicator.objects.create(
            symbol="AAPL", date=date(2024, 1, 15), close=185.0
        )
        mock_model = MagicMock()
        with patch("stocks.ml_predict.load_model", return_value=mock_model):
            result = predict_trend("AAPL")
        self.assertEqual(result["signal"], "UNKNOWN")
        self.assertIn("Missing features", result["reason"])

    def test_returns_buy_signal(self):
        StockIndicator.objects.create(
            symbol="AAPL", date=date(2024, 1, 15), close=185.0,
            rsi=55.0, sma_14=180.0, macd_line=1.5,
            bb_upper=195.0, bb_lower=175.0,
        )
        mock_model = MagicMock()
        mock_model.predict.return_value = [1]
        mock_model.predict_proba.return_value = [[0.2, 0.8]]

        with patch("stocks.ml_predict.load_model", return_value=mock_model):
            result = predict_trend("AAPL")

        self.assertIn("BUY", result["signal"])
        self.assertEqual(result["confidence"], 80.0)
        self.assertTrue(result["model_loaded"])

    def test_returns_sell_signal(self):
        StockIndicator.objects.create(
            symbol="TSLA", date=date(2024, 1, 15), close=200.0,
            rsi=75.0, sma_14=195.0, macd_line=-0.5,
            bb_upper=215.0, bb_lower=185.0,
        )
        mock_model = MagicMock()
        mock_model.predict.return_value = [0]
        mock_model.predict_proba.return_value = [[0.78, 0.22]]

        with patch("stocks.ml_predict.load_model", return_value=mock_model):
            result = predict_trend("TSLA")

        self.assertIn("SELL", result["signal"])
        self.assertEqual(result["confidence"], 78.0)


# ─────────────────────────────────────────────
# 4. API View Tests
# ─────────────────────────────────────────────

class StockPredictViewTest(TestCase):

    def test_predict_endpoint_returns_200(self):
        StockIndicator.objects.create(
            symbol="AAPL", date=date(2024, 1, 15), close=185.0,
            rsi=55.0, sma_14=180.0, macd_line=1.5,
            bb_upper=195.0, bb_lower=175.0,
        )
        mock_model = MagicMock()
        mock_model.predict.return_value = [1]
        mock_model.predict_proba.return_value = [[0.3, 0.7]]

        with patch("stocks.ml_predict.load_model", return_value=mock_model):
            response = self.client.get("/api/stocks/predict/?symbol=AAPL")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("signal", data)
        self.assertEqual(data["symbol"], "AAPL")

    def test_predict_endpoint_defaults_to_aapl(self):
        with patch("stocks.ml_predict.load_model", return_value=None):
            response = self.client.get("/api/stocks/predict/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["symbol"], "AAPL")