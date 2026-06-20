"""
ML prediction module for FinAPIx.
Loads a trained model and predicts tomorrow's price trend for a given symbol.
"""
import os
import joblib
import pandas as pd
import numpy as np

FEATURES = ['rsi', 'sma_14', 'macd_line', 'bb_upper', 'bb_lower']
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stock_trend_model.joblib')


def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    return joblib.load(MODEL_PATH)


def predict_trend(symbol: str):
    """
    Predict tomorrow's trend for a symbol using the latest indicator row.
    Returns dict: { signal, confidence, feature_values, model_loaded }
    """
    from stocks.models import StockIndicator

    model = load_model()
    if model is None:
        return {
            'signal': 'UNKNOWN',
            'confidence': None,
            'reason': 'Model not trained yet. Run: python train_model.py',
            'model_loaded': False,
        }

    latest = StockIndicator.objects.filter(symbol=symbol).order_by('-date').first()
    if latest is None:
        return {
            'signal': 'UNKNOWN',
            'confidence': None,
            'reason': f'No data in DB for {symbol}',
            'model_loaded': True,
        }

    row = {f: getattr(latest, f) for f in FEATURES}
    missing = [f for f, v in row.items() if v is None or (isinstance(v, float) and np.isnan(v))]
    if missing:
        return {
            'signal': 'UNKNOWN',
            'confidence': None,
            'reason': f'Missing features: {missing}',
            'model_loaded': True,
        }

    X = pd.DataFrame([row])
    prediction = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    confidence = round(float(max(proba)) * 100, 1)

    signal = 'BUY 📈' if prediction == 1 else 'SELL 📉'

    return {
        'signal': signal,
        'prediction': int(prediction),
        'confidence': confidence,
        'feature_values': row,
        'latest_date': str(latest.date),
        'model_loaded': True,
        'reason': None,
    }