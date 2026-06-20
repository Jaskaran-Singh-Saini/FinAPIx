from django.urls import path
from .views import StockDataView, StockPredictView

urlpatterns = [
    path('data/', StockDataView.as_view(), name='stock-data'),
    path('predict/', StockPredictView.as_view(), name='stock-predict'),
]