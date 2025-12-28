"""
Rating Conversion Module
------------------------
Converts sentiment polarity scores to star ratings (1-5).

Conversion Logic:
    Polarity Score → Star Rating
    > 0.6  → 5 stars (Highly Positive)
    > 0.3  → 4 stars (Positive)
    > 0.1  → 3 stars (Neutral/Slightly Positive)
    < 0    → 2 stars (Negative)
    else   → 1 star  (Highly Negative)

Design Philosophy:
    - Conservative approach: High bar for 5 stars
    - Neutral reviews (0.0-0.1) get 3 stars
    - Negative polarity always <= 2 stars
"""

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Rating thresholds (tunable based on business needs)
RATING_THRESHOLDS = {
    5: 0.6,   # Excellent - Strong positive sentiment
    4: 0.3,   # Good - Positive sentiment
    3: 0.1,   # Neutral - Slightly positive or neutral
    2: 0.0,   # Below Average - Negative sentiment
    1: -1.0   # Poor - Strong negative sentiment
}


def polarity_to_rating(polarity_score):
    """
    Convert polarity score to star rating (1-5).
    
    Args:
        polarity_score (float): Sentiment polarity (-1.0 to +1.0)
        
    Returns:
        int: Star rating (1-5)
        
    Algorithm:
        Uses descending threshold matching:
        - Start from 5 stars
        - Check if polarity meets threshold
        - Return first matching rating
        
    Examples:
        polarity_to_rating(0.85)  → 5 stars
        polarity_to_rating(0.45)  → 4 stars
        polarity_to_rating(0.15)  → 3 stars
        polarity_to_rating(-0.2)  → 2 stars
        polarity_to_rating(-0.8)  → 1 star
    """
    # Validate input
    if not isinstance(polarity_score, (int, float)):
        logger.warning(f"Invalid polarity score type: {type(polarity_score)}")
        return 3  # Default to neutral
    
    # Clamp polarity to valid range
    polarity_score = max(-1.0, min(1.0, polarity_score))
    
    # Apply threshold logic
    if polarity_score > RATING_THRESHOLDS[5]:
        return 5
    elif polarity_score > RATING_THRESHOLDS[4]:
        return 4
    elif polarity_score > RATING_THRESHOLDS[3]:
        return 3
    elif polarity_score >= RATING_THRESHOLDS[2]:
        return 2
    else:
        return 1


def rating_to_category(rating):
    """
    Convert star rating to human-readable category.
    
    Args:
        rating (int): Star rating (1-5)
        
    Returns:
        str: Rating category name
        
    Use Case:
        - Display on dashboard
        - Filtering/grouping reviews
        - Analytics reporting
    """
    categories = {
        5: 'Excellent',
        4: 'Good',
        3: 'Average',
        2: 'Below Average',
        1: 'Poor'
    }
    return categories.get(rating, 'Unknown')


def get_rating_distribution(polarity_scores):
    """
    Calculate rating distribution from multiple polarity scores.
    
    Args:
        polarity_scores (list): List of polarity scores
        
    Returns:
        dict: {
            'ratings': {1: count, 2: count, ...},
            'average_rating': float,
            'total_reviews': int,
            'distribution_percentage': {1: %, 2: %, ...}
        }
        
    Use Case:
        - Product/course analytics dashboard
        - Overall sentiment summary
        - Trend analysis
    """
    if not polarity_scores:
        return {
            'ratings': {i: 0 for i in range(1, 6)},
            'average_rating': 0.0,
            'total_reviews': 0,
            'distribution_percentage': {i: 0.0 for i in range(1, 6)}
        }
    
    # Convert all polarity scores to ratings
    ratings = [polarity_to_rating(score) for score in polarity_scores]
    
    # Count ratings
    rating_counts = {i: ratings.count(i) for i in range(1, 6)}
    
    # Calculate average
    total_reviews = len(ratings)
    average_rating = sum(ratings) / total_reviews if total_reviews > 0 else 0.0
    
    # Calculate percentage distribution
    distribution_pct = {
        i: round((count / total_reviews) * 100, 2) if total_reviews > 0 else 0.0
        for i, count in rating_counts.items()
    }
    
    return {
        'ratings': rating_counts,
        'average_rating': round(average_rating, 2),
        'total_reviews': total_reviews,
        'distribution_percentage': distribution_pct
    }


def calculate_review_score(sentiment_result):
    """
    Calculate comprehensive review score from sentiment analysis.
    
    Args:
        sentiment_result (dict): Output from sentiment.analyze_sentiment()
        
    Returns:
        dict: {
            'star_rating': int,
            'rating_category': str,
            'confidence': str,
            'sentiment_label': str,
            'polarity_score': float,
            'metadata': dict
        }
        
    Purpose:
        - Central function to convert AI output to user-facing metrics
        - Combines rating, confidence, and sentiment
        - Ready for database storage
    """
    polarity = sentiment_result.get('polarity_score', 0.0)
    label = sentiment_result.get('label', 'neutral')
    confidence = sentiment_result.get('score', 0.0)
    
    # Calculate star rating
    star_rating = polarity_to_rating(polarity)
    
    # Get rating category
    rating_category = rating_to_category(star_rating)
    
    # Determine confidence level
    if confidence >= 0.75:
        confidence_level = 'high'
    elif confidence >= 0.50:
        confidence_level = 'medium'
    else:
        confidence_level = 'low'
    
    return {
        'star_rating': star_rating,
        'rating_category': rating_category,
        'confidence': confidence_level,
        'sentiment_label': label,
        'polarity_score': polarity,
        'metadata': {
            'confidence_score': confidence,
            'raw_scores': sentiment_result.get('all_scores', {})
        }
    }


def adjust_rating_with_keywords(text, initial_rating):
    """
    Adjust rating based on specific keywords (business logic layer).
    
    Args:
        text (str): Review text
        initial_rating (int): Rating from polarity conversion
        
    Returns:
        Tuple[int, list]: (adjusted_rating, reasons)
        
    Business Rules:
        - Extreme negative keywords → Cap at 2 stars
        - Quality issues → -1 star adjustment
        - Exceptional service mentions → +1 star bonus
        
    Production Note:
        This function allows business stakeholders to define
        keyword-based rules without changing AI model.
        
    Example Rules:
        - "defective", "broken", "scam" → max 2 stars
        - "amazing", "best ever", "perfect" → bonus consideration
    """
    adjusted = initial_rating
    reasons = []
    
    text_lower = text.lower()
    
    # Extreme negative keywords (hard cap)
    extreme_negative = ['scam', 'fraud', 'defective', 'broken', 'terrible', 'worst']
    if any(word in text_lower for word in extreme_negative):
        if adjusted > 2:
            adjusted = 2
            reasons.append('extreme_negative_keywords')
    
    # Quality issue keywords
    quality_issues = ['poor quality', 'bad quality', 'not working', 'doesnt work']
    if any(phrase in text_lower for phrase in quality_issues) and adjusted > 2:
        adjusted = max(1, adjusted - 1)
        reasons.append('quality_issues')
    
    # Exceptional positive keywords (bonus for 4-star reviews)
    exceptional_positive = ['amazing', 'excellent', 'perfect', 'best ever', 'outstanding']
    if any(word in text_lower for word in exceptional_positive) and adjusted == 4:
        adjusted = 5
        reasons.append('exceptional_positive')
    
    return adjusted, reasons


def get_rating_color(rating):
    """
    Get color code for rating visualization (Bootstrap classes).
    
    Args:
        rating (int): Star rating (1-5)
        
    Returns:
        str: Bootstrap color class
        
    Use Case:
        - Frontend badge styling
        - Dashboard color coding
    """
    colors = {
        5: 'success',  # Green
        4: 'info',     # Blue
        3: 'warning',  # Yellow
        2: 'danger',   # Red
        1: 'danger'    # Red
    }
    return colors.get(rating, 'secondary')


def get_rating_emoji(rating):
    """
    Get emoji representation for rating.
    
    Args:
        rating (int): Star rating (1-5)
        
    Returns:
        str: Emoji character
    """
    emojis = {
        5: '🌟',
        4: '😊',
        3: '😐',
        2: '😞',
        1: '😢'
    }
    return emojis.get(rating, '⭐')