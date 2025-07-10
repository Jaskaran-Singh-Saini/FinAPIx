from rest_framework import serializers
from .models import StockIndicator

class StockIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockIndicator
        fields = '__all__'
        fields = ['symbol', 'date', 'close',
                   'rsi', 'sma_14', 'sma_20', 
                   'ema_20', 'wma_20', 'atr_14',
                   'obv', 'stochrsi', 
                   'macd_line', 'macd_signal',
                    'bb_upper', 'bb_middle', 'bb_lower',]