"""
Language Detection and Translation Module
-----------------------------------------
Handles Tamil/English detection and translation for sentiment analysis.
Uses langdetect for detection and Google Translate API for translation.

Author: AI Review System
Purpose: Multi-lingual review processing
"""

from langdetect import detect, LangDetectException
from googletrans import Translator
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Initialize translator as module-level singleton
_translator = None


def get_translator():
    """
    Lazy initialization of Google Translator.
    Prevents multiple instances and improves performance.
    """
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


@lru_cache(maxsize=500)
def detect_language(text):
    """
    Detect language of input text with caching.
    
    Args:
        text (str): Input review text
        
    Returns:
        str: Language code ('ta' for Tamil, 'en' for English, 'unknown' for errors)
        
    Performance Note:
        - Uses LRU cache to avoid repeated detection of similar texts
        - Cache size of 500 covers typical review patterns
    """
    if not text or len(text.strip()) < 3:
        return 'unknown'
    
    try:
        # langdetect works best with longer texts
        # Clean text for better detection
        clean_text = text.strip()
        lang_code = detect(clean_text)
        
        # Normalize language codes
        if lang_code in ['ta', 'tam']:
            return 'ta'
        elif lang_code in ['en', 'eng']:
            return 'en'
        else:
            # Default to English for unknown languages
            logger.warning(f"Detected unusual language: {lang_code}. Defaulting to English.")
            return 'en'
            
    except LangDetectException as e:
        logger.error(f"Language detection failed: {e}")
        return 'unknown'
    except Exception as e:
        logger.error(f"Unexpected error in language detection: {e}")
        return 'unknown'


def translate_to_english(text, source_lang='ta'):
    """
    Translate Tamil text to English for sentiment analysis.
    
    Args:
        text (str): Tamil text to translate
        source_lang (str): Source language code (default: 'ta')
        
    Returns:
        dict: {
            'translated_text': str,
            'original_text': str,
            'source_lang': str,
            'success': bool,
            'error': str (if failed)
        }
        
    Translation Strategy:
        - Uses Google Translate API (free tier)
        - Handles errors gracefully
        - Returns original text if translation fails
        
    Production Note:
        For high-volume production, consider:
        - AWS Translate
        - Azure Translator
        - DeepL API (better quality)
    """
    result = {
        'original_text': text,
        'translated_text': text,
        'source_lang': source_lang,
        'success': False,
        'error': None
    }
    
    try:
        translator = get_translator()
        translation = translator.translate(text, src=source_lang, dest='en')
        
        result['translated_text'] = translation.text
        result['success'] = True
        
        logger.info(f"Translation successful: {source_lang} -> en")
        
    except Exception as e:
        error_msg = f"Translation failed: {str(e)}"
        logger.error(error_msg)
        result['error'] = error_msg
        # Fallback: use original text
        result['translated_text'] = text
    
    return result


def process_review_text(text):
    """
    Complete preprocessing pipeline for review text.
    
    Args:
        text (str): Raw review text
        
    Returns:
        dict: {
            'processed_text': str,      # Text ready for sentiment analysis
            'original_text': str,       # Original input
            'detected_language': str,   # Language code
            'was_translated': bool,     # Whether translation occurred
            'translation_success': bool # Translation status
        }
        
    Pipeline:
        1. Detect language
        2. Translate if Tamil
        3. Return processed text for sentiment analysis
        
    Usage in views.py:
        processed = process_review_text(user_review)
        sentiment_result = analyze_sentiment(processed['processed_text'])
    """
    result = {
        'original_text': text,
        'processed_text': text,
        'detected_language': 'unknown',
        'was_translated': False,
        'translation_success': True
    }
    
    # Step 1: Detect language
    detected_lang = detect_language(text)
    result['detected_language'] = detected_lang
    
    # Step 2: Translate if needed
    if detected_lang == 'ta':
        translation_result = translate_to_english(text, source_lang='ta')
        result['processed_text'] = translation_result['translated_text']
        result['was_translated'] = True
        result['translation_success'] = translation_result['success']
    elif detected_lang == 'en':
        # Already English, no translation needed
        result['processed_text'] = text
    else:
        # Unknown language, try to process as-is
        logger.warning(f"Processing text with unknown language: {text[:50]}...")
        result['processed_text'] = text
    
    return result


# Utility function for bulk processing
def process_reviews_batch(reviews_list):
    """
    Process multiple reviews efficiently.
    
    Args:
        reviews_list (list): List of review texts
        
    Returns:
        list: List of processed review dictionaries
        
    Use Case:
        - Batch import of reviews
        - Migration of existing reviews
        - Periodic re-analysis
    """
    return [process_review_text(review) for review in reviews_list]