# stocks/utils.py

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from .models import StockIndicator

def fetch_and_save_stock_data(symbol):
    
    try:
        # --- NEW: Check if we have any data for this symbol ---
        is_initial_fetch = not StockIndicator.objects.filter(symbol=symbol).exists()
        
        if is_initial_fetch:
            print(f"📈 Initial fetch for {symbol}. Getting full 3-month history.")
        else:
            print(f"🔄 Daily update for {symbol}.")

        # Fetch 3 months of data for accurate indicator calculation
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

        # Calculate indicators
        df.ta.rsi(length=14, append=True)
        df.ta.sma(length=14, append=True)
        df.ta.macd(append=True)
        df.ta.bbands(length=20, std=2, append=True)

        # --- NEW: Decide how much data to process ---
        if is_initial_fetch:
            # For the first fetch, process the entire DataFrame
            data_to_process = df
        else:
            # For daily updates, only process the last 5 days for efficiency
            data_to_process = df.tail(5)
        
        created_count = 0
        updated_count = 0
        
        # Loop over the selected data (either the full history or just the last 5 days)
        for _, row in data_to_process.iterrows():
            if pd.isna(row["Date"]) or pd.isna(row["Close"]):
                continue

            obj, created = StockIndicator.objects.update_or_create(
                symbol=symbol,
                date=row["Date"].date(),
                defaults={
                    'close': row["Close"],
                    'rsi': row.get("RSI_14"),
                    'sma_14': row.get("SMA_14"),
                    'macd_line': row.get("MACD_12_26_9"),
                    'bb_upper': row.get("BBU_20_2.0_2.0"),
                    'bb_lower': row.get("BBL_20_2.0_2.0"),
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