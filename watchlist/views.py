from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Watchlist
from .serializers import WatchlistSerializer

# Create your views here.
class WatchlistView(generics.ListCreateAPIView):
    serializer_class = WatchlistSerializer
    permission_class = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WatchlistDetailView(generics.DestroyAPIView):
    serializer_class = WatchlistSerializer
    permission_class = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)