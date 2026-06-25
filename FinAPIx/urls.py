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
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import hello_view
from dashboard.views import stock_dashboard

# Swagger / ReDoc
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="FinAPIx API",
        default_version='v1',
        description="Stock Market Analysis Platform API — endpoints for stocks, watchlist, auth, and indicators.",
        contact=openapi.Contact(email="admin@finapix.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT Auth
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Apps
    path("hello/", hello_view, name="hello"),
    path("users/", include("users.urls")),
    path("watchlist/", include("watchlist.urls")),
    path("api/stocks/", include("stocks.urls")),
    path("dashboard/", include("dashboard.urls")),
    # path("accounts/", include("django.contrib.auth.urls")),

    # API Docs
    path("api/docs/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
    path("api/schema.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
]