"""
Django Models for AI-Powered Review System
------------------------------------------
Supports multi-entity reviews (Products & Courses) with full AI metadata.

Key Fix:
    ✔ Added GenericRelation to Product & Course
    ✔ Enables reverse queries like: product.reviews.all()
    ✔ Fixes: "Cannot resolve keyword 'reviews'" error
"""

from django.db import models
from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRelation
)
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator


# =============================================================================
# PRODUCT MODEL
# =============================================================================

class Product(models.Model):
    """E-commerce product model."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 FIX: reverse access to reviews
    reviews = GenericRelation(
        'Review',
        related_query_name='product'
    )

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.name

    def get_average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if not reviews.exists():
            return 0.0
        return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 2)

    def get_review_count(self):
        return self.reviews.filter(is_approved=True).count()

    def get_sentiment_distribution(self):
        reviews = self.reviews.filter(is_approved=True)
        total = reviews.count()

        if total == 0:
            return {'positive': 0, 'neutral': 0, 'negative': 0}

        return {
            'positive': round(reviews.filter(sentiment='positive').count() * 100 / total, 1),
            'neutral': round(reviews.filter(sentiment='neutral').count() * 100 / total, 1),
            'negative': round(reviews.filter(sentiment='negative').count() * 100 / total, 1),
        }


# =============================================================================
# COURSE MODEL
# =============================================================================

class Course(models.Model):
    """Online course model."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructor = models.CharField(max_length=100)
    duration_hours = models.IntegerField(null=True, blank=True)

    level = models.CharField(
        max_length=50,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )

    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    thumbnail_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # 🔥 FIX: reverse access to reviews
    reviews = GenericRelation(
        'Review',
        related_query_name='course'
    )

    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['instructor']),
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return f"{self.title} by {self.instructor}"

    def get_average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if not reviews.exists():
            return 0.0
        return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 2)

    def get_review_count(self):
        return self.reviews.filter(is_approved=True).count()

    def get_sentiment_distribution(self):
        reviews = self.reviews.filter(is_approved=True)
        total = reviews.count()

        if total == 0:
            return {'positive': 0, 'neutral': 0, 'negative': 0}

        return {
            'positive': round(reviews.filter(sentiment='positive').count() * 100 / total, 1),
            'neutral': round(reviews.filter(sentiment='neutral').count() * 100 / total, 1),
            'negative': round(reviews.filter(sentiment='negative').count() * 100 / total, 1),
        }


# =============================================================================
# REVIEW MODEL (GENERIC)
# =============================================================================

class Review(models.Model):
    """Universal review model using GenericForeignKey."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    review_text = models.TextField()
    reviewer_name = models.CharField(max_length=100, blank=True)
    reviewer_email = models.EmailField(blank=True)

    sentiment = models.CharField(
        max_length=20,
        choices=[('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')],
        db_index=True
    )

    polarity_score = models.FloatField(
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)]
    )

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True
    )

    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('ta', 'Tamil'), ('unknown', 'Unknown')],
        default='unknown',
        db_index=True
    )

    translated_text = models.TextField(blank=True)
    was_translated = models.BooleanField(default=False)

    is_suspicious = models.BooleanField(default=False, db_index=True)
    suspicious_flags = models.JSONField(default=list, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    is_approved = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['sentiment', 'rating']),
            models.Index(fields=['is_approved']),
        ]

    def __str__(self):
        return f"{self.content_type.model.capitalize()} Review ({self.rating}★)"


# =============================================================================
# REVIEW SUMMARY MODEL
# =============================================================================

class ReviewSummary(models.Model):
    """Precomputed analytics for dashboard."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    total_reviews = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    average_polarity = models.FloatField(default=0.0)

    positive_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)
    negative_count = models.IntegerField(default=0)

    rating_5_count = models.IntegerField(default=0)
    rating_4_count = models.IntegerField(default=0)
    rating_3_count = models.IntegerField(default=0)
    rating_2_count = models.IntegerField(default=0)
    rating_1_count = models.IntegerField(default=0)

    suspicious_reviews_count = models.IntegerField(default=0)
    average_confidence = models.FloatField(default=0.0)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review_summaries'
        unique_together = [['content_type', 'object_id']]

    def __str__(self):
        return f"Summary for {self.content_type.model} {self.object_id}"
