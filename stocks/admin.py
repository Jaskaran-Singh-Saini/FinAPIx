from django.contrib import admin
from .models import StockIndicator

# Register your models here.

@admin.register(StockIndicator)
class stockIndicatorAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'date', 'close', 'rsi', 'sma_14', 'macd_line')
    list_filter = ('symbol', 'date')