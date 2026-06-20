from django.shortcuts import render
from stocks.models import StockIndicator, TrackedStock
from .forms import StockFilterForm
from stocks.utils import fetch_and_save_stock_data
from datetime import datetime
from watchlist.models import Watchlist
import json
import math
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


def stock_dashboard(request):
    symbol = request.GET.get("symbol", "AAPL").upper()
    start_date = request.GET.get("start")
    end_date = request.GET.get("end")

    # Step 1: Check DB
    data_qs = StockIndicator.objects.filter(symbol=symbol).order_by("date")

    # Step 2: Fetch from yfinance if empty
    if not data_qs.exists():
        if fetch_and_save_stock_data(symbol):
            data_qs = StockIndicator.objects.filter(symbol=symbol).order_by("date")
        else:
            return render(request, "dashboard/dashboard.html", {
                "form": StockFilterForm(),
                "chart_data": "{}",
                "symbol": symbol,
                "data": [],
                "start": start_date,
                "end": end_date,
                "error": f"No data available for {symbol}. Please check the symbol."
            })

    # Step 3: Filter by date range if provided
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            data_qs = data_qs.filter(date__range=(start, end))
        except Exception as e:
            print(f"⚠️ Invalid date range: {e}")

    # Step 4: Handle no results after filter
    if not data_qs.exists():
        return render(request, "dashboard/dashboard.html", {
            "form": StockFilterForm(request.GET or None),
            "chart_data": "{}",
            "symbol": symbol,
            "data": [],
            "start": start_date,
            "end": end_date,
            "error": "No data found for the selected date range."
        })

    # Step 5: Build chart data
    chart_data = build_chart_data(symbol, data_qs)

    user_watchlist = []
    if request.user.is_authenticated:
        user_watchlist = Watchlist.objects.filter(user=request.user).values_list('symbol', flat=True)

    # ML Prediction
    from stocks.ml_predict import predict_trend
    prediction = predict_trend(symbol)

    # Step 6: Render final response
    return render(request, "dashboard/dashboard.html", {
        "form": StockFilterForm(request.GET or None),
        "chart_data": json.dumps(chart_data),
        "symbol": symbol.upper(),
        "data": data_qs,
        "start": start_date,
        "end": end_date,
        "user_watchlist": user_watchlist,
        "prediction": prediction,
    })

def clean_data(values):
    """Replace NaN or None with None (to become null in JSON)."""
    return [None if (v is None or (isinstance(v, float) and math.isnan(v))) else v for v in values]


def build_chart_data(symbol, data_qs):
    labels = [entry.date.strftime("%Y-%m-%d") for entry in data_qs]

    closes = clean_data([entry.close for entry in data_qs])
    macd_line = clean_data([entry.macd_line for entry in data_qs])
    rsi = clean_data([entry.rsi for entry in data_qs])
    sma_14 = clean_data([entry.sma_14 for entry in data_qs])

    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": f"{symbol} Closing Prices",
                "data": closes,
                "borderColor": "rgba(75, 192, 192, 1)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "fill": False,
                "tension": 0.1
            },
            {
                "label": "MACD Line",
                "data": macd_line,
                "borderColor": "rgba(255, 99, 132, 1)",
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "fill": False,
                "tension": 0.1
            },
            {
                "label": "RSI",
                "data": rsi,
                "borderColor": "rgba(153, 102, 255, 1)",
                "backgroundColor": "rgba(153, 102, 255, 0.2)",
                "fill": False,
                "tension": 0.1
            },
            {
                "label": "SMA 14",
                "data": sma_14,
                "borderColor": "rgba(255, 206, 86, 1)",
                "backgroundColor": "rgba(255, 206, 86, 0.2)",
                "fill": False,
                "tension": 0.1
            }
        ]
    }

    return chart_data


@login_required
def get_chart_data(request, symbol):
    """AJAX endpoint for chart refresh without page reload"""
    data_qs = StockIndicator.objects.filter(symbol=symbol).order_by("date")

    if not data_qs.exists():
        if not fetch_and_save_stock_data(symbol):
            return JsonResponse({"error": f"No data available for {symbol}"}, status=404)
        data_qs = StockIndicator.objects.filter(symbol=symbol).order_by("date")

    chart_data = build_chart_data(symbol, data_qs)
    return JsonResponse(chart_data)


@login_required
def dashboard_view(request):
    tracked_symbols = TrackedStock.objects.filter(user=request.user).values_list('symbol', flat=True)
    indicators = StockIndicator.objects.filter(symbol__in=tracked_symbols).order_by('date')

    all_symbols = StockIndicator.objects.values_list('symbol', flat=True).distinct()
    user_symbols = list(tracked_symbols)

    return render(request, 'dashboard/dashboard.html', {
        'indicators': indicators,
        'all_symbols': all_symbols,
        'user_symbols': user_symbols,
    })
