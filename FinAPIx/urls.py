"""
URL configuration for FinAPIx project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from users.views import hello_view
from dashboard.views import stock_dashboard


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("hello/", hello_view, name="hello"),
    path("users/", include("users.urls")),
    path("watchlist/", include("watchlist.urls")),
    path("api/stocks/", include("stocks.urls")),
    # FinAPIx/urls.py
    path("dashboard/", stock_dashboard, name="stock_dashboard"),
    
    path('accounts/', include('django.contrib.auth.urls')),

    path('users/', include("users.urls")),
    path('', include("stocks.urls")),
]
