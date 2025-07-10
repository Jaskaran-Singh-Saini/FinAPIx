import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
from .models import StockIndicator

def fetch_and_save_stock_data(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period = "3mo")
    if data is None or data.empty:
        return
    
    data.reset_index(inplace = True)
    data['Date'] = data['Date'].astype(str)
    data['RSI'] = ta.rsi(data['Close'], length=14)
    data['SMA_14'] = ta.sma(data['Close'],length=14)
    data['SMA_20'] = ta.sma(data['Close'], length=20)
    data['EMA_20'] = ta.ema(data['Close'], length=20)
    data['WMA_20'] = ta.wma(data['Close'], length=20)
    data['ATR_14'] = ta.atr(high=data['High'], low=data['Low'], close=data['Close'], length=14)
    data['OBV'] = ta.obv(close = data['Close'], volume=data['Volume'])

    stochrsi = ta.stochrsi(data['Close'], length=14)
    if stochrsi is not None:
        if 'STOCHRSIk_14_14_3_3' in stochrsi.columns:
            data['StochRSI'] = stochrsi['STOCHRSIk_14_14_3_3']
        elif 'STOCHRSIk_14_14_3' in stochrsi.columns:
            data['StochRSI'] = stochrsi['STOCHRSIk_14_14_3']
        else:
            data['StochRSI'] = 0  # fallback to 0 if not found
    else:
        data['StochRSI'] = 0

    macd = ta.macd(data['Close'])
    if macd is not None:
        data = data.join(macd[['MACD_12_26_9', 'MACDs_12_26_9']])
        data.rename(columns = {'MACD_12_26_9': 'MACD_Line', 'MACDs_12_26_9':'MACD_Signal'}, inplace=True)

    bb = ta.bbands(data['Close'], length=20)
    if bb is not None:
        data['BB_upper'] = bb['BBU_20_2.0']
        data['BB_middle'] = bb['BBM_20_2.0']
        data['BB_lower'] = bb['BBL_20_2.0']

    data.replace([np.inf, -np.inf], np.nan, inplace = True)
    data.fillna(0, inplace = True)

    for index, row in data.iterrows():
        if row['SMA_20'] == 0 or row['MACD_Line'] == 0 or row['RSI'] == 0:
            continue

        StockIndicator.objects.update_or_create(
            symbol = symbol,
            date = pd.to_datetime(row['Date']).date(),
            defaults={
                'close' : row['Close'],
                'rsi' : row['RSI'],
                'sma_14' : row['SMA_14'],
                'sma_20' : row['SMA_20'],
                'ema_20' : row['EMA_20'],
                'wma_20' : row['WMA_20'],
                'atr_14' : row['ATR_14'],
                'obv' : row['OBV'],
                'stochrsi' : row['StochRSI'],
                'macd_line' : row['MACD_Line'],
                'macd_signal' : row['MACD_Signal'],
                'bb_upper' : row['BB_upper'],
                'bb_middle' : row['BB_middle'],
                'bb_lower' : row['BB_lower'],
            }
        )  