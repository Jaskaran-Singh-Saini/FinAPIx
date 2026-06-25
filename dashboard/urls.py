from django.urls import path
from . import views

urlpatterns = [
    path('', views.stock_dashboard, name='stock_dashboard'),
    path('chart-data/<str:symbol>/', views.get_chart_data, name='chart-data'),
    path('refresh/<str:symbol>/', views.refresh_stock, name='refresh_stock'),
]