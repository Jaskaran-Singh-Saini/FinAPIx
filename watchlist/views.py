from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions
from .models import Watchlist
from .serializers import WatchlistSerializer
from django.urls import reverse
from django.http import JsonResponse


@method_decorator(login_required, name='dispatch')
class WatchlistView(generics.ListCreateAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Watchlist.objects.none()
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WatchlistDetailView(generics.DestroyAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Watchlist.objects.none()
        return Watchlist.objects.filter(user=self.request.user)


@login_required
def watchlist_page(request):
    watchlist_items = Watchlist.objects.filter(user=request.user)
    return render(request, "watchlist/watchlist_list.html", {"watchlist_items": watchlist_items})


@login_required
def add_to_watchlist(request, symbol):
    Watchlist.objects.get_or_create(user=request.user, symbol=symbol.upper())
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "symbol": symbol})
    return redirect(f"{reverse('stock_dashboard')}?symbol={symbol}")


@login_required
def remove_from_watchlist(request, symbol):
    Watchlist.objects.filter(user=request.user, symbol=symbol.upper()).delete()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "symbol": symbol})
    return redirect(f"{reverse('stock_dashboard')}?symbol={symbol}")


@login_required
def watchlist_list(request):
    watchlist_items = Watchlist.objects.filter(user=request.user)
    return render(request, 'watchlist/watchlist_list.html', {'watchlist_items': watchlist_items})