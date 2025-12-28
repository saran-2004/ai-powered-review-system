# AI-Powered Review Analytics Platform

An AI-driven web application built with Django that analyzes customer reviews to extract sentiment, ratings, and suspicious behavior insights.  
The platform provides an interactive dashboard for visual analytics and supports standalone bulk review ingestion via CSV upload.

## Features

- Sentiment analysis (Positive, Neutral, Negative)
- Automatic rating prediction (1–5 stars)
- Suspicious / fake review detection
- Interactive analytics dashboard with charts
- Advanced filtering (sentiment, rating, time range)
- Secure login and logout system
- Role-ready architecture (admin vs viewer)
- Standalone CSV upload for bulk review analysis
- Django Admin support for data management

---

## Technology Stack

- Backend: Django (Python)
- Frontend: HTML, Bootstrap, Chart.js
- Database: SQLite
- AI / NLP: Transformers (RoBERTa-based sentiment model)
- Authentication: Django Auth
- Version Control: Git & GitHub
---

## Dashboard Capabilities

- Real-time review analytics
- Sentiment distribution pie chart
- Rating distribution bar chart
- Filter reviews by:
  - Sentiment
  - Rating
  - Time range (Today, 7 days, 30 days)
- Displays suspicious review count
- Auto-refresh based on filters

---

## Standalone Review Upload

The platform supports CSV upload for bulk review processing.

### CSV Format

```csv
review_text
This product is excellent and very useful.
Worst experience, not recommended.
## Installation & Setup

Follow these steps to run the project locally:

```bash
# Clone the repository
git clone https://github.com/saran-2004/ai-powered-review-system.git
cd ai-powered-review-system

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r ai_review_system/requirements.txt

# Apply database migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start the development server
python manage.py runserver
Dashboard: http://127.0.0.1:8000/reviews/

Admin panel: http://127.0.0.1:8000/admin/
