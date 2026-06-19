from django.urls import path
from .views import RegisterView, hello_view, register_view, login_view, logout_view
from rest_framework_simplejwt.tokens import RefreshToken

urlpatterns = [
    path('api/register/', RegisterView.as_view(), name='register'),
    path('hello/', hello_view, name='hello'),
    path('register/', register_view, name="register"),
    path('login/', login_view, name="login"),
    path('logout/', logout_view, name="logout"),
]