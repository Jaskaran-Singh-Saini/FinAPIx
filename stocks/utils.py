# stocks/utils.py

import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD
from ta.volatility import BollingerBands
from .models import StockIndicator

def fetch_and_save_stock_data(symbol):
    try:
        is_initial_fetch = not StockIndicator.objects.filter(symbol=symbol).exists()

        if is_initial_fetch:
            print(f"📈 Initial fetch for {symbol}. Getting full 6-month history.")
        else:
            print(f"🔄 Daily update for {symbol}.")

        df = yf.download(tickers=symbol, period="6mo", interval="1d", progress=False, group_by="column")

        if df.empty:
            print(f"❌ No data available for {symbol} from yfinance.")
            return f"No data for {symbol}"

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df['Date'] = df.index
        df.reset_index(drop=True, inplace=True)

        if "Date" not in df.columns or "Close" not in df.columns:
            print("❌ Required columns missing in fetched data.")
            return "Missing columns"

        close = df["Close"]

        # Calculate indicators
        df["RSI_14"]      = RSIIndicator(close=close, window=14).rsi()
        df["SMA_14"]      = SMAIndicator(close=close, window=14).sma_indicator()
        macd              = MACD(close=close)
        df["MACD_12_26_9"]= macd.macd()
        bb                = BollingerBands(close=close, window=20, window_dev=2)
        df["BBU_20"]      = bb.bollinger_hband()
        df["BBL_20"]      = bb.bollinger_lband()

        data_to_process = df if is_initial_fetch else df.tail(5)

        created_count = 0
        updated_count = 0

        for _, row in data_to_process.iterrows():
            if pd.isna(row["Date"]) or pd.isna(row["Close"]):
                continue

            obj, created = StockIndicator.objects.update_or_create(
                symbol=symbol,
                date=row["Date"].date(),
                defaults={
                    'close':      row["Close"],
                    'rsi':        row.get("RSI_14"),
                    'sma_14':     row.get("SMA_14"),
                    'macd_line':  row.get("MACD_12_26_9"),
                    'bb_upper':   row.get("BBU_20"),
                    'bb_lower':   row.get("BBL_20"),
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        result_msg = f"✅ {symbol}: {created_count} new, {updated_count} updated."
        print(result_msg)
        return result_msg

    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return f"Error: {e}"