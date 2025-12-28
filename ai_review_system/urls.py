from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    # Admin panel
    path("admin/", admin.site.urls),

    # 🔐 Django auth URLs (login, logout, password reset)
    path("", include("django.contrib.auth.urls")),

    # Reviews app
    path("reviews/", include("reviews.urls")),

    # Root redirect → dashboard
    path("", lambda request: redirect("reviews:dashboard")),
]
