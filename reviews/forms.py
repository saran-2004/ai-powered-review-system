"""
Django Forms for Review System
------------------------------
Provides user-facing forms with validation and AI preprocessing.

Forms:
    - ReviewForm: Main review submission form
    - ProductForm: Product creation (admin)
    - CourseForm: Course creation (admin)
    - ReviewFilterForm: Dashboard filtering
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Review, Product, Course
import re


class ReviewForm(forms.ModelForm):
    """
    Main review submission form with AI preprocessing.
    
    Features:
        - Client-side validation (Django)
        - Spam prevention
        - Character limit enforcement
        - Clean UI with Bootstrap classes
    """
    
    # Override fields for custom widgets and validation
    review_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Write your review here... (Tamil or English)',
            'maxlength': 2000,
            'required': True
        }),
        label='Your Review',
        max_length=2000,
        min_length=10,
        help_text='Minimum 10 characters, maximum 2000 characters. Tamil and English supported.',
        error_messages={
            'required': 'Please write a review before submitting.',
            'min_length': 'Review must be at least 10 characters long.',
            'max_length': 'Review cannot exceed 2000 characters.'
        }
    )
    
    reviewer_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name (optional)'
        }),
        label='Name',
        max_length=100,
        required=False,
        help_text='Optional: Your name will be displayed with the review.'
    )
    
    reviewer_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com (optional)'
        }),
        label='Email',
        required=False,
        help_text='Optional: We may contact you for follow-up.'
    )
    
    class Meta:
        model = Review
        fields = ['review_text', 'reviewer_name', 'reviewer_email']
    
    def clean_review_text(self):
        """
        Validate and sanitize review text.
        
        Checks:
            1. Minimum meaningful content
            2. No spam patterns
            3. No excessive repetition
            4. No URL spam (optional)
        """
        text = self.cleaned_data.get('review_text', '').strip()
        
        # Check minimum word count
        word_count = len(text.split())
        if word_count < 3:
            raise ValidationError('Review must contain at least 3 words.')
        
        # Check for excessive repetition (spam indicator)
        words = text.lower().split()
        if len(words) > 5:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            if repetition_ratio < 0.3:  # Less than 30% unique words
                raise ValidationError(
                    'Review appears to contain excessive repetition. '
                    'Please write a more detailed review.'
                )
        
        # Check for URL spam (optional - uncomment if needed)
        # url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        # if re.findall(url_pattern, text):
        #     raise ValidationError('URLs are not allowed in reviews.')
        
        # Check for excessive punctuation
        punctuation_count = sum(1 for char in text if char in '!?')
        if punctuation_count > 10:
            raise ValidationError(
                'Please reduce excessive punctuation in your review.'
            )
        
        return text
    
    def clean_reviewer_email(self):
        """Validate email format and check for disposable domains."""
        email = self.cleaned_data.get('reviewer_email', '').strip()
        
        if not email:
            return email
        
        # Optional: Block disposable email domains
        disposable_domains = [
            'tempmail.com', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email'
        ]
        
        email_domain = email.split('@')[-1].lower()
        if email_domain in disposable_domains:
            raise ValidationError(
                'Disposable email addresses are not allowed. '
                'Please use a permanent email address.'
            )
        
        return email


class ProductForm(forms.ModelForm):
    """
    Product creation/edit form for admin.
    """
    
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Product name'
        }),
        max_length=200
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Product description'
        }),
        required=False
    )
    
    category = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Electronics, Clothing, Books'
        }),
        max_length=100,
        required=False
    )
    
    price = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        max_digits=10,
        decimal_places=2,
        required=False
    )
    
    image_url = forms.URLField(
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com/image.jpg'
        }),
        required=False,
        help_text='URL to product image'
    )
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'price', 'image_url']
    
    def clean_price(self):
        """Ensure price is positive."""
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise ValidationError('Price cannot be negative.')
        return price


class CourseForm(forms.ModelForm):
    """
    Course creation/edit form for admin.
    """
    
    LEVEL_CHOICES = [
        ('', 'Select level'),
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ]
    
    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Course title'
        }),
        max_length=200
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Course description'
        }),
        required=False
    )
    
    instructor = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Instructor name'
        }),
        max_length=100
    )
    
    duration_hours = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Duration in hours',
            'min': 1
        }),
        required=False,
        help_text='Total course duration in hours'
    )
    
    level = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        choices=LEVEL_CHOICES,
        required=False
    )
    
    price = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        max_digits=10,
        decimal_places=2,
        required=False
    )
    
    thumbnail_url = forms.URLField(
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com/thumbnail.jpg'
        }),
        required=False,
        help_text='URL to course thumbnail'
    )
    
    class Meta:
        model = Course
        fields = ['title', 'description', 'instructor', 'duration_hours', 
                  'level', 'price', 'thumbnail_url']
    
    def clean_duration_hours(self):
        """Ensure duration is positive."""
        duration = self.cleaned_data.get('duration_hours')
        if duration and duration < 1:
            raise ValidationError('Duration must be at least 1 hour.')
        return duration
    
    def clean_price(self):
        """Ensure price is positive."""
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise ValidationError('Price cannot be negative.')
        return price


class ReviewFilterForm(forms.Form):
    """
    Filter form for dashboard and review list.
    
    Filters:
        - Sentiment (positive/neutral/negative)
        - Rating (1-5 stars)
        - Language (Tamil/English)
        - Date range
        - Suspicious reviews only
    """
    
    SENTIMENT_CHOICES = [
        ('', 'All Sentiments'),
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative')
    ]
    
    RATING_CHOICES = [
        ('', 'All Ratings'),
        ('5', '5 Stars'),
        ('4', '4 Stars'),
        ('3', '3 Stars'),
        ('2', '2 Stars'),
        ('1', '1 Star')
    ]
    
    LANGUAGE_CHOICES = [
        ('', 'All Languages'),
        ('en', 'English'),
        ('ta', 'Tamil')
    ]
    
    sentiment = forms.ChoiceField(
        choices=SENTIMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    show_suspicious_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Show suspicious reviews only'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='From Date'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='To Date'
    )
    
    def clean(self):
        """Validate date range."""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError('End date must be after start date.')
        
        return cleaned_data