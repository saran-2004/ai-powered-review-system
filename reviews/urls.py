"""
URL Configuration for Reviews App
---------------------------------
Standalone AI Review Intelligence Platform
"""

from django.urls import path
from . import views
from . import views_standalone

app_name = "reviews"

urlpatterns = [
    # ==============================
    # DASHBOARD (ALL LOGGED-IN USERS)
    # ==============================
    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    # ==============================
    # STANDALONE INPUT (ADMIN ONLY)
    # ==============================
    path(
        "upload/",
        views_standalone.upload_reviews,
        name="upload_reviews"
    ),

    # ==============================
    # REVIEW SUBMISSION (ADMIN ONLY)
    # ==============================
    path(
        "submit/<str:entity_type>/<int:entity_id>/",
        views.submit_review,
        name="submit_review"
    ),

    # ==============================
    # REVIEW LISTING (ALL USERS)
    # ==============================
    path(
        "list/",
        views.review_list,
        name="review_list_all"
    ),
    path(
        "list/<str:entity_type>/<int:entity_id>/",
        views.review_list,
        name="review_list"
    ),

    # ==============================
    # PRODUCT & COURSE ANALYTICS
    # ==============================
    path(
        "products/",
        views.product_list,
        name="product_list"
    ),
    path(
        "courses/",
        views.course_list,
        name="course_list"
    ),
]
