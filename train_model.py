import os
import django
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FinAPIx.settings')
django.setup()

from stocks.models import StockIndicator

def prepare_data(symbol: str):
    """Fetches and DEBUGs the data for the ML model."""
    print(f"--- Preparing data for {symbol} ---")
    qs = StockIndicator.objects.filter(symbol=symbol).order_by('date').values()
    
    if not qs.exists():
        print(f"❌ No data found in the database for {symbol}.")
        return None, None
        
    df = pd.DataFrame(list(qs))
    print(f"\nLoaded {len(df)} records from the database.")
    
    print("\n[DEBUG] DataFrame Info (shows data types and non-null counts):")
    df.info() 
    
    print("\n[DEBUG] Count of Null/NaN values in each column:")
    print(df.isnull().sum())
    
    df['TomorrowClose'] = df['close'].shift(-1)
    df['Trend'] = (df['TomorrowClose'] > df['close']).astype(int)
    
    df.dropna(inplace=True)
    
    if df.empty:
        print(f"\n❌ No clean data remaining for {symbol} after preparing features.")
        return None, None

    features = ['rsi', 'sma_14', 'macd_line', 'bb_upper', 'bb_lower']
    X = df[features]
    y = df['Trend']
    
    print("\n✅ Data preparation complete.")
    return X, y

def train_and_evaluate(X, y):
    print("\n--- Training and Evaluating Model ---")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    print("Training the model...")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"📊 Model Accuracy: {accuracy:.2%}")
    return model

def save_model(model, filename="stock_trend_model.joblib"):
    print(f"\n--- Saving Model to {filename} ---")
    joblib.dump(model, filename)
    print(f"✅ Model saved successfully.")

if __name__ == "__main__":
    STOCK_SYMBOL = 'RELIANCE.NS'
    X_data, y_data = prepare_data(STOCK_SYMBOL)
    if X_data is not None and y_data is not None:
        trained_model = train_and_evaluate(X_data, y_data)
        save_model(trained_model)