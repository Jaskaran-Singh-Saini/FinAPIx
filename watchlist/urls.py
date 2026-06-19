from django.contrib import admin
from django.urls import path, include
from .views import (
    WatchlistView, WatchlistDetailView,
    watchlist_page, add_to_watchlist, remove_from_watchlist,
    add_to_watchlist, remove_from_watchlist
    )
from . import views

urlpatterns = [
    # API URLs
    path('api/', WatchlistView.as_view(), name='watchlist'),
    path('api/<int:pk>/',WatchlistDetailView.as_view(), name='watchlist-delete'),

    # Template-based views
    path("", watchlist_page, name="watchlist_page"),
    path("add/<str:symbol>/", add_to_watchlist, name="add_to_watchlist"),
    path("remove/<str:symbol>/", remove_from_watchlist, name="remove_from_watchlist"),

    path('list/', views.watchlist_list, name='watchlist_list'),

]