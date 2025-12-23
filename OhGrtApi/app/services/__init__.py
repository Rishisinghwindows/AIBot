"""
Services module - External API integrations and business logic

Contains services for:
- Weather: weather_service.py
- News: news_service.py
- Travel (Railway): travel_service.py
- Image Generation: image_service.py
- Astrology: astrology_service.py
- Firebase: firebase_service.py
- Gmail: gmail_service.py
- Postgres: postgres_service.py
- RAG: rag_service.py
- Tavily: tavily_service.py
- And more...
"""

from app.services.weather_service import WeatherService
from app.services.news_service import NewsService, get_news_service
from app.services.travel_service import TravelService, get_travel_service, get_pnr_status, get_train_status
from app.services.image_service import generate_image, generate_image_async

__all__ = [
    "WeatherService",
    "NewsService",
    "get_news_service",
    "TravelService",
    "get_travel_service",
    "get_pnr_status",
    "get_train_status",
    "generate_image",
    "generate_image_async",
]
