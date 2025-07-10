from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    symbol = models.CharField(max_length=10)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user','symbol']

    def __str__(self):
        return f"{self.user.username} - {self.symbol}"
        