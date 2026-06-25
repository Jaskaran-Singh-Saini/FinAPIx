from django.shortcuts import render
import yfinance as yf
import pandas as pd
import numpy as np
import json
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import SMAIndicator, EMAIndicator, WMAIndicator, MACD
from ta.volatility import AverageTrueRange, BollingerBands
from ta.volume import OnBalanceVolumeIndicator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from datetime import datetime, timedelta
from django.http import JsonResponse
from .models import StockIndicator
from .serializers import StockIndicatorSerializer
from django.utils.dateparse import parse_datetime


class StockDataView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        symbol = request.query_params.get('symbol', 'AAPL')

        existing_data = StockIndicator.objects.filter(symbol=symbol).order_by('-date')
        if existing_data.exists():
            serializer = StockIndicatorSerializer(existing_data, many=True)
            return JsonResponse(serializer.data, safe=False)

        stock = yf.Ticker(symbol)
        data = stock.history(period="3mo")
        if data is None or data.empty:
            return JsonResponse({"error": f"No data found for symbol {symbol}"}, status=404)

        data.reset_index(inplace=True)
        data['Date'] = data['Date'].astype(str)

        close  = data['Close']
        high   = data['High']
        low    = data['Low']
        volume = data['Volume']

        # RSI and SMAs
        data['RSI']    = RSIIndicator(close, window=14).rsi()
        data['SMA_14'] = SMAIndicator(close, window=14).sma_indicator()
        data['SMA_20'] = SMAIndicator(close, window=20).sma_indicator()

        # EMA, WMA, ATR, OBV
        data['EMA_20'] = EMAIndicator(close, window=20).ema_indicator()
        data['WMA_20'] = WMAIndicator(close, window=20).wma()
        data['ATR_14'] = AverageTrueRange(high, low, close, window=14).average_true_range()
        data['OBV']    = OnBalanceVolumeIndicator(close, volume).on_balance_volume()

        # Stochastic RSI
        stochrsi = StochRSIIndicator(close, window=14)
        data['StochRSI'] = stochrsi.stochrsi_k()

        # MACD
        macd = MACD(close)
        data['MACD_Line']   = macd.macd()
        data['MACD_Signal'] = macd.macd_signal()

        # Bollinger Bands
        bb = BollingerBands(close, window=20, window_dev=2)
        data['BB_upper']  = bb.bollinger_hband()
        data['BB_middle'] = bb.bollinger_mavg()
        data['BB_lower']  = bb.bollinger_lband()

        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        data.fillna(0, inplace=True)

        saved_count   = 0
        skipped_count = 0
        total_rows    = len(data)

        for index, row in data.iterrows():
            if (
                pd.isna(row['SMA_20']) or row['SMA_20'] == 0 or
                pd.isna(row['MACD_Line']) or row['MACD_Line'] == 0 or
                pd.isna(row['RSI']) or row['RSI'] == 0
            ):
                skipped_count += 1
                continue

            StockIndicator.objects.create(
                symbol      = symbol,
                date        = pd.to_datetime(row['Date']).date(),
                close       = row['Close'],
                rsi         = row['RSI'],
                sma_14      = row['SMA_14'],
                sma_20      = row['SMA_20'],
                ema_20      = row['EMA_20'],
                wma_20      = row['ATR_14'],
                obv         = row['OBV'],
                stochrsi    = row['StochRSI'],
                macd_line   = row['MACD_Line'],
                macd_signal = row['MACD_Signal'],
                bb_upper    = row['BB_upper'],
                bb_middle   = row['BB_middle'],
                bb_lower    = row['BB_lower'],
            )
            saved_count += 1

        print(f"Total rows: {total_rows}, Saved: {saved_count}, Skipped: {skipped_count}")

        saved_data = StockIndicator.objects.filter(symbol=symbol).order_by('date')
        serializer = StockIndicatorSerializer(saved_data, many=True)
        return JsonResponse(serializer.data, safe=False)


class StockPredictView(APIView):
    """
    GET /api/stocks/predict/?symbol=AAPL
    Returns ML-based trend prediction for tomorrow.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from .ml_predict import predict_trend
        symbol = request.query_params.get('symbol', 'AAPL').upper()
        result = predict_trend(symbol)
        result['symbol'] = symbol
        return Response(result)