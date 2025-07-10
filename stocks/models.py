from django.db import models

# Create your models here.
class StockIndicator(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    close = models.FloatField()
    rsi = models.FloatField(null=True, blank=True)
    sma_14 = models.FloatField(null=True, blank=True)
    sma_20 = models.FloatField(null=True, blank=True)
    ema_20 = models.FloatField(null=True, blank=True)
    wma_20 = models.FloatField(null=True, blank=True)
    atr_14 = models.FloatField(null=True, blank=True)
    obv = models.FloatField(null=True, blank=True)
    stochrsi = models.FloatField(null=True, blank=True)
    macd_line = models.FloatField(null=True, blank=True)
    macd_signal = models.FloatField(null=True, blank=True)
    bb_upper = models.FloatField(null=True, blank=True)
    bb_middle =models.FloatField(null=True, blank=True)
    bb_lower = models.FloatField(null=True, blank=True)
    class Meta:
        unique_together = ('symbol', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.symbol} - {self.date}"