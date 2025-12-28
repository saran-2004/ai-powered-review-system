from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg, Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Review, Product, Course, ReviewSummary
from .forms import ReviewForm

# 🔥 ROLE DECORATOR (NEW)
from .decorators import admin_required

from .ai.language import process_review_text
from .ai.sentiment import analyze_sentiment, detect_fake_review_indicators
from .ai.rating import calculate_review_score

logger = logging.getLogger(__name__)

# =============================================================================
# DASHBOARD (ALL LOGGED-IN USERS)
# =============================================================================

@login_required
def dashboard(request):
    reviews = Review.objects.filter(is_approved=True)

    sentiment = request.GET.get("sentiment")
    rating = request.GET.get("rating")
    days = request.GET.get("days")

    if sentiment:
        reviews = reviews.filter(sentiment=sentiment)

    if rating:
        reviews = reviews.filter(rating=int(rating))

    if days:
        reviews = reviews.filter(
            created_at__gte=timezone.now() - timedelta(days=int(days))
        )

    sentiment_stats = {
        "positive": reviews.filter(sentiment="positive").count(),
        "neutral": reviews.filter(sentiment="neutral").count(),
        "negative": reviews.filter(sentiment="negative").count(),
    }

    rating_stats = [
        reviews.filter(rating=1).count(),
        reviews.filter(rating=2).count(),
        reviews.filter(rating=3).count(),
        reviews.filter(rating=4).count(),
        reviews.filter(rating=5).count(),
    ]

    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"] or 0

    context = {
        "total_reviews": reviews.count(),
        "avg_rating": avg_rating,
        "sentiment_stats": sentiment_stats,
        "rating_stats": rating_stats,
        "suspicious_count": reviews.filter(is_suspicious=True).count(),
        "selected_sentiment": sentiment,
        "selected_rating": rating,
        "selected_days": days,
    }

    return render(request, "reviews/dashboard.html", context)

# =============================================================================
# REVIEW SUBMISSION (ADMIN ONLY)
# =============================================================================

@admin_required
def submit_review(request, entity_type, entity_id):
    if entity_type == "product":
        entity = get_object_or_404(Product, id=entity_id)
        content_type = ContentType.objects.get_for_model(Product)
    elif entity_type == "course":
        entity = get_object_or_404(Course, id=entity_id)
        content_type = ContentType.objects.get_for_model(Course)
    else:
        messages.error(request, "Invalid entity.")
        return redirect("reviews:dashboard")

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review_text = form.cleaned_data["review_text"]

            try:
                language_result = process_review_text(review_text)
                sentiment_result = analyze_sentiment(language_result["processed_text"])
                rating_result = calculate_review_score(sentiment_result)
                fake_result = detect_fake_review_indicators(review_text, sentiment_result)
            except Exception:
                language_result = {
                    "processed_text": review_text,
                    "detected_language": "unknown",
                    "was_translated": False
                }
                sentiment_result = {
                    "label": "neutral",
                    "polarity_score": 0.0,
                    "score": 0.0
                }
                rating_result = {"star_rating": 3}
                fake_result = {"is_suspicious": False, "flags": []}

            review = form.save(commit=False)
            review.content_type = content_type
            review.object_id = entity.id
            review.sentiment = sentiment_result["label"]
            review.polarity_score = sentiment_result["polarity_score"]
            review.confidence_score = sentiment_result["score"]
            review.rating = rating_result["star_rating"]
            review.language = language_result["detected_language"]
            review.was_translated = language_result["was_translated"]
            review.translated_text = language_result.get("processed_text", "")
            review.is_suspicious = fake_result["is_suspicious"]
            review.suspicious_flags = fake_result["flags"]
            review.is_approved = True
            review.save()

            update_review_summary(content_type, entity.id)
            return redirect("reviews:dashboard")

    else:
        form = ReviewForm()

    return render(request, "reviews/review_form.html", {
        "form": form,
        "entity": entity,
        "entity_type": entity_type,
    })

# =============================================================================
# REVIEW LIST (ALL USERS)
# =============================================================================

@login_required
def review_list(request, entity_type=None, entity_id=None):
    reviews = Review.objects.filter(is_approved=True).order_by("-created_at")

    if entity_type and entity_id:
        model = Product if entity_type == "product" else Course
        content_type = ContentType.objects.get_for_model(model)
        reviews = reviews.filter(content_type=content_type, object_id=entity_id)

    paginator = Paginator(reviews, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "reviews/review_list.html", {"reviews": page_obj})

# =============================================================================
# PRODUCT & COURSE LIST (ALL USERS)
# =============================================================================

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, "reviews/product_list.html", {"products": products})


@login_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, "reviews/course_list.html", {"courses": courses})

# =============================================================================
# REVIEW SUMMARY (INTERNAL)
# =============================================================================

def update_review_summary(content_type, object_id):
    reviews = Review.objects.filter(
        content_type=content_type,
        object_id=object_id,
        is_approved=True
    )

    if not reviews.exists():
        return

    summary, _ = ReviewSummary.objects.get_or_create(
        content_type=content_type,
        object_id=object_id
    )

    stats = reviews.aggregate(
        total=Count("id"),
        avg_rating=Avg("rating"),
        positive=Count("id", filter=Q(sentiment="positive")),
        neutral=Count("id", filter=Q(sentiment="neutral")),
        negative=Count("id", filter=Q(sentiment="negative")),
    )

    summary.total_reviews = stats["total"]
    summary.average_rating = stats["avg_rating"] or 0
    summary.positive_count = stats["positive"]
    summary.neutral_count = stats["neutral"]
    summary.negative_count = stats["negative"]
    summary.save()
