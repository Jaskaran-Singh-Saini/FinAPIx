from django.db import models
from django.contrib.auth.models import User

class StockIndicator(models.Model):
    symbol = models.CharField(max_length=20)
    date = models.DateField()
    close = models.FloatField()
    
    rsi = models.FloatField(null=True, blank=True)
    sma_14 = models.FloatField(null=True, blank=True)
    macd_line = models.FloatField(null=True, blank=True)
    bb_upper = models.FloatField(null=True, blank=True)
    bb_lower = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ('symbol', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.symbol} - {self.date}"

class TrackedStock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tracked_stocks')
    symbol = models.CharField(max_length=20) 

    class Meta:
        unique_together = ('user', 'symbol')

    def __str__(self):
        return f"{self.user.username} - {self.symbol}"