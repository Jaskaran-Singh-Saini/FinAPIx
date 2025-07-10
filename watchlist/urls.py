from django.urls import path
from .views import WatchlistView, WatchlistDetailView

urlpatterns = [
    path('', WatchlistView.as_view(), name='watchlist'),
    path('<int:pk>/',WatchlistDetailView.as_view(), name='watchlist-delete'),
]