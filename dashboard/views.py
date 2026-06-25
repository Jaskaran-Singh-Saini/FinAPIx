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

QUICK_SYMBOLS = ["AAPL", "TSLA", "MSFT", "GOOGL", "NVDA"]


def is_nan(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def stock_dashboard(request):
    symbol = request.GET.get("symbol", "AAPL").upper()
    start_date = request.GET.get("start")
    end_date = request.GET.get("end")

    data_qs = StockIndicator.objects.filter(symbol=symbol).order_by("date")

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
                "quick_symbols": QUICK_SYMBOLS,
                "error": f"No data available for {symbol}. Please check the symbol."
            })

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            data_qs = data_qs.filter(date__range=(start, end))
        except Exception as e:
            print(f"⚠️ Invalid date range: {e}")

    if not data_qs.exists():
        return render(request, "dashboard/dashboard.html", {
            "form": StockFilterForm(request.GET or None),
            "chart_data": "{}",
            "symbol": symbol,
            "data": [],
            "start": start_date,
            "end": end_date,
            "quick_symbols": QUICK_SYMBOLS,
            "error": "No data found for the selected date range."
        })

    chart_data = build_chart_data(symbol, data_qs)

    # Table: only show rows where RSI is available (enough history)
    table_data = [e for e in data_qs if not is_nan(e.rsi)]

    user_watchlist = []
    if request.user.is_authenticated:
        user_watchlist = Watchlist.objects.filter(user=request.user).values_list('symbol', flat=True)

    from stocks.ml_predict import predict_trend
    prediction = predict_trend(symbol)

    return render(request, "dashboard/dashboard.html", {
        "form": StockFilterForm(request.GET or None),
        "chart_data": json.dumps(chart_data),
        "symbol": symbol.upper(),
        "data": table_data,
        "start": start_date,
        "end": end_date,
        "user_watchlist": user_watchlist,
        "prediction": prediction,
        "quick_symbols": QUICK_SYMBOLS,
    })


def clean_data(values):
    return [None if is_nan(v) else v for v in values]


def is_nan(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def build_chart_data(symbol, data_qs):
    labels   = [entry.date.strftime("%Y-%m-%d") for entry in data_qs]
    closes   = clean_data([entry.close     for entry in data_qs])
    sma14    = clean_data([entry.sma_14    for entry in data_qs])
    bb_upper = clean_data([entry.bb_upper  for entry in data_qs])
    bb_lower = clean_data([entry.bb_lower  for entry in data_qs])
    rsi      = clean_data([entry.rsi       for entry in data_qs])
    macd     = clean_data([entry.macd_line for entry in data_qs])

    return {
        "labels":   labels,
        "closes":   closes,
        "sma14":    sma14,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "rsi":      rsi,
        "macd":     macd,
    }


@login_required
def get_chart_data(request, symbol):
    data_qs = StockIndicator.objects.filter(symbol=symbol).order_by("date")
    if not data_qs.exists():
        if not fetch_and_save_stock_data(symbol):
            return JsonResponse({"error": f"No data available for {symbol}"}, status=404)
        data_qs = StockIndicator.objects.filter(symbol=symbol).order_by("date")
    return JsonResponse(build_chart_data(symbol, data_qs))


@login_required
def dashboard_view(request):
    tracked_symbols = TrackedStock.objects.filter(user=request.user).values_list('symbol', flat=True)
    indicators = StockIndicator.objects.filter(symbol__in=tracked_symbols).order_by('date')
    all_symbols = StockIndicator.objects.values_list('symbol', flat=True).distinct()
    return render(request, 'dashboard/dashboard.html', {
        'indicators': indicators,
        'all_symbols': list(all_symbols),
        'user_symbols': list(tracked_symbols),
        'quick_symbols': QUICK_SYMBOLS,
    })

@login_required
def refresh_stock(request, symbol):
    """Manual refresh endpoint — replaces Celery beat in production."""
    if request.method == "POST":
        result = fetch_and_save_stock_data(symbol.upper())
        return JsonResponse({"success": True, "message": result})
    return JsonResponse({"success": False, "message": "POST required"}, status=405)