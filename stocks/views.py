from django.shortcuts import render
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from datetime import datetime, timedelta
from django.http import JsonResponse
from .models import StockIndicator
from .serializers import StockIndicatorSerializer
from django.utils.dateparse import parse_datetime

# Create your views here.
class StockDataView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        symbol = request.query_params.get('symbol', 'AAPL')

        # Get latest record from DB for that symbol
        existing_data = StockIndicator.objects.filter(symbol=symbol).order_by('-date')

        # If data exists in DB, return it
        if existing_data.exists():
            serializer = StockIndicatorSerializer(existing_data, many=True)
            return JsonResponse(serializer.data, safe=False)

        stock = yf.Ticker(symbol)
        data = stock.history(period="3mo")
        if data is None or data.empty:
            return JsonResponse({"error": f"No data found for symbol {symbol}"}, status=404)

        data.reset_index(inplace=True)
        data['Date'] = data['Date'].astype(str)

        #calculate RSI and SMA
        data['RSI'] = ta.rsi(data['Close'], length=14)
        data['SMA_14'] = ta.sma(data['Close'], length=14)
        data['SMA_20'] = ta.sma(data['Close'], length=20)

        #calculate EMA, WMA, ATR and OBV
        data['EMA_20'] = ta.ema(data['Close'], length = 20)
        data['WMA_20'] = ta.wma(data['Close'], length = 20)
        atr = ta.atr(high=data['High'], low=data['Low'], close=data['Close'], length=14)
        data['ATR_14'] = atr
        obv = ta.obv(close=data['Close'], volume=data['Volume'])
        data['OBV'] = obv

        
        # Stochastic RSI
        stochrsi = ta.stochrsi(data['Close'], length=14)
        if stochrsi is not None:
            data['StochRSI'] = stochrsi['STOCHRSIk_14_14_3_3']

        #MACD (returns full dataframes, we extract 2 columns)
        macd = ta.macd(data['Close'])
        if macd is not None and 'MACD_12_26_9' in macd.columns and 'MACDs_12_26_9' in macd.columns:
            data = data.join(macd[['MACD_12_26_9', 'MACDs_12_26_9']])
            data.rename(columns={'MACD_12_26_9': 'MACD_Line', 'MACDs_12_26_9': 'MACD_Signal'}, inplace=True)
        else:
            data['MACD_Line'] = 0
            data['MACD_Signal'] = 0

        #Bollinger Bands
        bb = ta.bbands(data['Close'], length=20)
        if bb is not None:
            data['BB_upper'] = bb['BBU_20_2.0']
            data['BB_middle'] = bb['BBM_20_2.0']
            data['BB_lower'] = bb['BBL_20_2.0']
        else:
            data['BB_upper'] = data['BB_middle'] = data['BB_lower'] = 0

        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        data.fillna(0, inplace=True) #Alternative : fillna(0)

        saved_count = 0
        skipped_count = 0
        total_rows = len(data)

        for index, row in data.iterrows():
            if (
                    pd.isna(row['SMA_20']) or row['SMA_20'] == 0 or
                    pd.isna(row['MACD_Line']) or row['MACD_Line'] == 0 or
                    pd.isna(row['RSI']) or row['RSI'] == 0
                ):
                skipped_count +=1
                continue
            #Checking if saving only Non-zero values or not
            #print(f"Saving: {row['Date']} - Close: {row['Close']} - RSI: {row['RSI']}")
            StockIndicator.objects.create(
                symbol = symbol,
                date = pd.to_datetime(row['Date']).date(),
                close = row['Close'],
                rsi = row['RSI'],
                sma_14 = row['SMA_14'],
                sma_20 = row['SMA_20'],
                ema_20 = row['EMA_20'],
                wma_20 = row['ATR_14'],
                obv = row['OBV'],
                stochrsi = row['StochRSI'],
                macd_line = row['MACD_Line'],
                macd_signal = row['MACD_Signal'],
                bb_upper = row['BB_upper'],
                bb_middle = row['BB_middle'],
                bb_lower = row['BB_lower'],
            )

            saved_count += 1
        print(f"Total rows: {total_rows}, Saved: {saved_count}, Skipped: {skipped_count}")


        saved_data = StockIndicator.objects.filter(symbol=symbol).order_by('date')
        serializer = StockIndicatorSerializer(saved_data, many=True)
        return JsonResponse(serializer.data, safe=False)
