from django.urls import path
from .views import RegisterView, HelloView
from rest_framework_simplejwt.tokens import RefreshToken
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('hello/', HelloView.as_view(), name='hello'),
]