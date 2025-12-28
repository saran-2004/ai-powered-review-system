import csv
from django.shortcuts import render, redirect
from django.contrib import messages

# 🔐 ROLE-BASED ACCESS
from .decorators import admin_required

from .models import Review
from .ai.language import process_review_text
from .ai.sentiment import analyze_sentiment, detect_fake_review_indicators
from .ai.rating import calculate_review_score


# =============================================================================
# CSV UPLOAD – ADMIN ONLY (STANDALONE MODE)
# =============================================================================

@admin_required   # 🔥 THIS IS THE KEY LINE
def upload_reviews(request):
    if request.method == "POST":
        file = request.FILES.get("file")

        if not file:
            messages.error(request, "Please upload a CSV file.")
            return redirect("reviews:upload_reviews")

        try:
            reader = csv.DictReader(
                file.read().decode("utf-8").splitlines()
            )
        except Exception:
            messages.error(request, "Invalid CSV file.")
            return redirect("reviews:upload_reviews")

        created_count = 0

        for row in reader:
            review_text = row.get("review_text", "").strip()
            if not review_text:
                continue

            # ---------------- AI ANALYSIS (SAFE) ----------------
            try:
                language_result = process_review_text(review_text)
                sentiment_result = analyze_sentiment(
                    language_result["processed_text"]
                )
                rating_result = calculate_review_score(sentiment_result)
                fake_result = detect_fake_review_indicators(
                    review_text, sentiment_result
                )
            except Exception:
                # Fallback (NEVER CRASH)
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
            # ---------------------------------------------------

            Review.objects.create(
                review_text=review_text,
                sentiment=sentiment_result["label"],
                polarity_score=sentiment_result["polarity_score"],
                confidence_score=sentiment_result["score"],
                rating=rating_result["star_rating"],
                language=language_result["detected_language"],
                was_translated=language_result["was_translated"],
                translated_text=language_result.get("processed_text", ""),
                is_suspicious=fake_result["is_suspicious"],
                suspicious_flags=fake_result["flags"],
                is_approved=True
            )

            created_count += 1

        messages.success(
            request,
            f"{created_count} reviews uploaded and analyzed successfully!"
        )
        return redirect("reviews:dashboard")

    return render(request, "reviews/upload_reviews.html")
