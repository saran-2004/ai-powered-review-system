"""
Sentiment Analysis Module using HuggingFace Transformers
--------------------------------------------------------
Uses cardiffnlp/twitter-roberta-base-sentiment model for state-of-the-art
sentiment classification.

Model Details:
- Pre-trained on 58M tweets
- Fine-tuned for sentiment analysis
- Labels: negative (0), neutral (1), positive (2)
- Robust to informal language and emojis

Performance Optimizations:
- Singleton pattern for model loading
- GPU acceleration if available
- Batch processing support
"""

from transformers import AutoModelForSequenceClassification, AutoTokenizer
from scipy.special import softmax
import torch
import logging
import numpy as np
from functools import lru_cache

logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"
SENTIMENT_LABELS = ['negative', 'neutral', 'positive']

# Global model cache (singleton pattern)
_model = None
_tokenizer = None
_device = None


def initialize_model():
    """
    Load and cache the sentiment analysis model.
    
    Implementation Notes:
        - Loads model once at startup
        - Automatically detects GPU availability
        - Uses CPU as fallback
        
    Production Optimization:
        - In production, use model quantization for faster inference
        - Consider ONNX runtime for deployment
        - Use GPU instances (AWS p3, Azure NC series)
    """
    global _model, _tokenizer, _device
    
    if _model is None:
        try:
            logger.info(f"Loading sentiment model: {MODEL_NAME}")
            
            # Detect device (GPU/CPU)
            _device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f"Using device: {_device}")
            
            # Load tokenizer and model
            _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
            
            # Move model to device
            _model.to(_device)
            _model.eval()  # Set to evaluation mode
            
            logger.info("Sentiment model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            raise RuntimeError(f"Model initialization failed: {e}")
    
    return _model, _tokenizer, _device


def analyze_sentiment(text, return_all_scores=False):
    """
    Analyze sentiment of text using RoBERTa transformer model.
    
    Args:
        text (str): Input text (pre-processed, English)
        return_all_scores (bool): If True, return scores for all labels
        
    Returns:
        dict: {
            'label': str,              # 'positive', 'neutral', 'negative'
            'score': float,            # Confidence score (0-1)
            'polarity_score': float,   # Normalized score (-1 to +1)
            'all_scores': dict,        # Scores for all labels (optional)
            'raw_logits': list         # Raw model outputs (for debugging)
        }
        
    Polarity Score Mapping:
        - Positive: 0.0 to +1.0
        - Neutral: close to 0.0
        - Negative: -1.0 to 0.0
        
    Example:
        result = analyze_sentiment("This product is amazing!")
        # {'label': 'positive', 'score': 0.95, 'polarity_score': 0.90}
    """
    
    # Validate input
    if not text or not isinstance(text, str):
        return {
            'label': 'neutral',
            'score': 0.0,
            'polarity_score': 0.0,
            'error': 'Invalid input text'
        }
    
    try:
        # Initialize model if not already loaded
        model, tokenizer, device = initialize_model()
        
        # Tokenize input text
        # max_length=512 is RoBERTa's limit
        encoded_input = tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # Move input to device
        encoded_input = {k: v.to(device) for k, v in encoded_input.items()}
        
        # Get model predictions
        with torch.no_grad():
            output = model(**encoded_input)
            
        # Extract logits and convert to probabilities
        logits = output.logits[0].cpu().numpy()
        scores = softmax(logits)
        
        # Get dominant sentiment
        ranking = np.argsort(scores)[::-1]
        top_label_idx = ranking[0]
        
        label = SENTIMENT_LABELS[top_label_idx]
        confidence = float(scores[top_label_idx])
        
        # Calculate polarity score (-1 to +1)
        # Formula: (positive_score - negative_score)
        polarity = float(scores[2] - scores[0])
        
        result = {
            'label': label,
            'score': round(confidence, 4),
            'polarity_score': round(polarity, 4),
            'raw_logits': logits.tolist()
        }
        
        # Include all scores if requested
        if return_all_scores:
            result['all_scores'] = {
                SENTIMENT_LABELS[i]: round(float(scores[i]), 4)
                for i in range(len(SENTIMENT_LABELS))
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {
            'label': 'neutral',
            'score': 0.0,
            'polarity_score': 0.0,
            'error': str(e)
        }


def batch_analyze_sentiment(texts, batch_size=8):
    """
    Analyze sentiment for multiple texts efficiently.
    
    Args:
        texts (list): List of text strings
        batch_size (int): Number of texts to process at once
        
    Returns:
        list: List of sentiment result dictionaries
        
    Performance:
        - 5-10x faster than individual processing
        - GPU utilization improves with larger batches
        - Optimal batch_size: 8-32 depending on text length
        
    Use Cases:
        - Analyzing existing reviews after deployment
        - Batch import from external systems
        - Periodic re-analysis for model updates
    """
    results = []
    
    try:
        model, tokenizer, device = initialize_model()
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Tokenize batch
            encoded = tokenizer(
                batch,
                return_tensors='pt',
                truncation=True,
                max_length=512,
                padding=True
            )
            
            encoded = {k: v.to(device) for k, v in encoded.items()}
            
            # Get predictions
            with torch.no_grad():
                output = model(**encoded)
            
            # Process each result in batch
            logits = output.logits.cpu().numpy()
            
            for j, text_logits in enumerate(logits):
                scores = softmax(text_logits)
                top_idx = np.argmax(scores)
                
                results.append({
                    'label': SENTIMENT_LABELS[top_idx],
                    'score': round(float(scores[top_idx]), 4),
                    'polarity_score': round(float(scores[2] - scores[0]), 4),
                    'text': batch[j]
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Batch sentiment analysis failed: {e}")
        return [
            {'label': 'neutral', 'score': 0.0, 'polarity_score': 0.0, 'error': str(e)}
            for _ in texts
        ]


def get_sentiment_confidence_level(score):
    """
    Classify confidence level of sentiment prediction.
    
    Args:
        score (float): Confidence score (0-1)
        
    Returns:
        str: 'high', 'medium', 'low'
        
    Thresholds:
        - High: score >= 0.75 (very confident)
        - Medium: 0.50 <= score < 0.75 (moderately confident)
        - Low: score < 0.50 (uncertain)
        
    Use Case:
        - Flagging uncertain predictions for manual review
        - Quality control in production
    """
    if score >= 0.75:
        return 'high'
    elif score >= 0.50:
        return 'medium'
    else:
        return 'low'


def detect_fake_review_indicators(text, sentiment_result):
    """
    Basic fake review detection based on text patterns.
    
    Args:
        text (str): Review text
        sentiment_result (dict): Result from analyze_sentiment()
        
    Returns:
        dict: {
            'is_suspicious': bool,
            'flags': list,
            'confidence': float
        }
        
    Detection Heuristics:
        1. Extreme polarity (very positive/negative)
        2. Very short reviews with extreme sentiment
        3. Excessive punctuation (!!!, ???)
        4. All caps text
        5. Low confidence with extreme language
        
    Production Enhancement:
        - Train ML model on known fake reviews
        - Check review velocity (multiple reviews from same user)
        - Analyze review patterns across products
        - Use NLP features: readability, authenticity scores
    """
    flags = []
    
    # Check extreme polarity
    polarity = sentiment_result.get('polarity_score', 0)
    if abs(polarity) > 0.85:
        flags.append('extreme_polarity')
    
    # Check text length vs sentiment strength
    if len(text.split()) < 5 and abs(polarity) > 0.7:
        flags.append('short_extreme_review')
    
    # Check excessive punctuation
    if text.count('!') > 3 or text.count('?') > 3:
        flags.append('excessive_punctuation')
    
    # Check all caps (ignoring short texts)
    if len(text) > 20 and text.isupper():
        flags.append('all_caps')
    
    # Check low confidence with extreme language
    confidence = sentiment_result.get('score', 0)
    if confidence < 0.6 and abs(polarity) > 0.7:
        flags.append('uncertain_extreme')
    
    is_suspicious = len(flags) >= 2  # At least 2 flags = suspicious
    
    return {
        'is_suspicious': is_suspicious,
        'flags': flags,
        'confidence': round(len(flags) / 5, 2)  # Normalize to 0-1
    }