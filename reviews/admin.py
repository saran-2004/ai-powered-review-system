from django.contrib import admin
from .models import Product, Course, Review, ReviewSummary

# =============================================================================
# PRODUCT ADMIN
# =============================================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'created_at')
    search_fields = ('name', 'category')


# =============================================================================
# COURSE ADMIN
# =============================================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'instructor', 'level', 'price')
    search_fields = ('title', 'instructor')


# =============================================================================
# REVIEW ADMIN (🔥 FIXED)
# =============================================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'content_object',
        'rating',
        'sentiment',
        'language',
        'is_approved',
        'is_suspicious',
        'created_at',
    )

    list_filter = (
        'is_approved',
        'sentiment',
        'language',
        'is_suspicious',
        'created_at',
    )

    search_fields = ('review_text', 'reviewer_name', 'reviewer_email')

    list_editable = ('is_approved',)   # ✅ THIS ENABLES INLINE APPROVAL

    actions = ['approve_reviews']      # ✅ BULK APPROVAL

    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(
            request,
            f"{updated} review(s) approved successfully."
        )

    approve_reviews.short_description = "Approve selected reviews"


# =============================================================================
# REVIEW SUMMARY ADMIN
# =============================================================================

@admin.register(ReviewSummary)
class ReviewSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'content_object',
        'total_reviews',
        'average_rating',
        'last_updated',
    )
