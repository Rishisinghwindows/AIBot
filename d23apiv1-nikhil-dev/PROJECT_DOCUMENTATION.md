# D23Bot - WhatsApp Astrology Bot

## Project Overview

D23Bot is an AI-powered WhatsApp chatbot specializing in Vedic astrology, with additional utility features like weather, news, travel information, and more. Built with LangGraph for stateful conversation management and FastAPI for webhook handling.

**Version:** 2.0.0
**Tech Stack:** Python 3.12, FastAPI, LangGraph, PostgreSQL, OpenAI

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   WhatsApp      │────▶│   FastAPI        │────▶│   LangGraph     │
│   Cloud API     │◀────│   Webhook        │◀────│   State Machine │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                        ┌─────────────────────────────────┼─────────────────────────────────┐
                        │                                 │                                 │
                        ▼                                 ▼                                 ▼
                ┌───────────────┐              ┌───────────────┐              ┌───────────────┐
                │  Intent       │              │  Node         │              │  Tools        │
                │  Detection    │              │  Handlers     │              │  (APIs)       │
                └───────────────┘              └───────────────┘              └───────────────┘
```

### Flow
1. WhatsApp sends webhook to `/webhook` endpoint
2. FastAPI validates signature and parses message
3. LangGraph processes message through state machine:
   - Intent Detection → Route to Handler → Generate Response
4. Response sent back via WhatsApp Cloud API

---

## Project Structure

```
D23Bot/
├── main.py                      # FastAPI application entry point
├── bot/
│   ├── __init__.py
│   ├── config.py                # Settings and environment variables
│   ├── state.py                 # LangGraph state definitions
│   ├── graph.py                 # Main LangGraph workflow (V1)
│   ├── graph_v2.py              # Domain-based routing (V2)
│   │
│   ├── constants/
│   │   └── intents.py           # Intent patterns and keywords
│   │
│   ├── nodes/                   # LangGraph node handlers
│   │   ├── intent.py            # Intent detection node
│   │   ├── chat.py              # General chat & fallback
│   │   ├── astro_node.py        # Horoscope, birth chart, etc.
│   │   ├── dosha_node.py        # Manglik, Kaal Sarp dosha
│   │   ├── life_prediction_node.py  # Career, marriage predictions
│   │   ├── subscription_node.py # Subscription management
│   │   ├── weather.py           # Weather queries
│   │   ├── news_node.py         # News headlines
│   │   ├── pnr_status.py        # PNR status check
│   │   ├── train_status.py      # Train running status
│   │   ├── metro_ticket.py      # Metro route/fare
│   │   ├── local_search.py      # Nearby places search
│   │   ├── image_gen.py         # AI image generation
│   │   ├── reminder_node.py     # Reminders
│   │   ├── word_game.py         # Word games
│   │   └── db_node.py           # Database queries
│   │
│   ├── tools/                   # External API integrations
│   │   ├── astro_tool.py        # Astrology calculations
│   │   ├── dosha_tool.py        # Dosha calculations
│   │   ├── life_prediction_tool.py
│   │   ├── weather_api.py       # OpenWeatherMap
│   │   ├── news_tool.py         # News API
│   │   ├── railway_api.py       # Indian Railways
│   │   ├── metro_api.py         # Delhi Metro
│   │   ├── tavily_search.py     # Web search
│   │   ├── fal_image.py         # FAL AI image gen
│   │   ├── reminder_tool.py     # Reminder scheduling
│   │   ├── word_game.py         # Word game logic
│   │   ├── db_tool.py           # Database operations
│   │   └── rag_tool.py          # RAG retrieval
│   │
│   ├── services/                # Background services
│   │   ├── __init__.py
│   │   ├── subscription_service.py  # Subscription CRUD
│   │   ├── horoscope_scheduler.py   # Daily horoscope sender
│   │   ├── transit_service.py       # Planetary transit alerts
│   │   └── reminder_service.py      # Reminder scheduler
│   │
│   ├── stores/                  # Data persistence
│   │   ├── __init__.py
│   │   ├── base_store.py        # Abstract store interface
│   │   ├── postgres_store.py    # PostgreSQL implementation
│   │   └── memory_store.py      # In-memory (LITE_MODE)
│   │
│   ├── whatsapp/                # WhatsApp integration
│   │   ├── webhook.py           # Webhook handler
│   │   ├── client.py            # WhatsApp Cloud API client
│   │   └── signature.py         # HMAC signature verification
│   │
│   ├── i18n/                    # Internationalization
│   │   ├── __init__.py
│   │   ├── translator.py        # Translation engine
│   │   ├── templates/           # Response templates
│   │   └── locales/             # Language files (22 languages)
│   │
│   ├── utils/                   # Utilities
│   │   ├── response_formatter.py    # Response formatting
│   │   ├── validators.py            # Input validation
│   │   ├── rate_limiter.py          # Rate limiting
│   │   └── entity_extractor.py      # Entity extraction
│   │
│   └── graphs/                  # Sub-graphs
│       └── domain_classifier.py # Domain classification
│
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── test_integration.py      # Integration tests
│   ├── test_subscription.py     # Subscription tests
│   ├── test_validators.py       # Validator tests
│   ├── test_rate_limiter.py     # Rate limiter tests
│   └── test_domain_classifier.py
│
├── test_bot_logic.py            # Logic validation script
├── test_subscription_quick.py   # Quick subscription tests
├── pytest.ini                   # Pytest configuration
├── requirements.txt             # Dependencies
├── .env.example                 # Environment template
└── PROJECT_DOCUMENTATION.md     # This file
```

---

## Configuration

### Environment Variables (.env)

```bash
# =============================================================================
# MODE
# =============================================================================
LITE_MODE=false                    # true = in-memory store, no schedulers

# =============================================================================
# WHATSAPP CLOUD API
# =============================================================================
WHATSAPP_PHONE_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_APP_SECRET=your_app_secret    # For webhook signature verification
WEBHOOK_VERIFY_TOKEN=your_verify_token

# =============================================================================
# DATABASE (PostgreSQL)
# =============================================================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=d23bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# =============================================================================
# AI/ML APIS
# =============================================================================
OPENAI_API_KEY=sk-...
FAL_API_KEY=your_fal_key              # Image generation

# =============================================================================
# EXTERNAL APIS
# =============================================================================
OPENWEATHER_API_KEY=your_key
NEWS_API_KEY=your_key
TAVILY_API_KEY=your_key               # Web search
RAPIDAPI_KEY=your_key                 # Railways API

# =============================================================================
# OPTIONAL
# =============================================================================
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379      # For rate limiting (optional)
```

### Settings (bot/config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Mode
    LITE_MODE: bool = False

    # WhatsApp
    WHATSAPP_PHONE_ID: str
    WHATSAPP_ACCESS_TOKEN: str
    WHATSAPP_APP_SECRET: str = ""
    WEBHOOK_VERIFY_TOKEN: str = "verify_token"

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "d23bot"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""

    # AI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Features & Intents

### Astrology Domain

| Intent | Description | Example Queries |
|--------|-------------|-----------------|
| `get_horoscope` | Daily/weekly/monthly horoscope | "Aries horoscope", "Leo rashifal today" |
| `birth_chart` | Generate Kundli | "Kundli for 15-08-1990 10:30 AM Delhi" |
| `kundli_matching` | Match two charts | "Match kundli Rahul and Priya" |
| `dosha_check` | Check doshas | "Check mangal dosha", "Am I manglik?" |
| `life_prediction` | Life predictions | "When will I get married?", "Career prediction" |
| `numerology` | Numerology reading | "Numerology for Rahul Kumar" |
| `tarot_reading` | Tarot card reading | "Tarot reading for career" |
| `get_panchang` | Daily Panchang | "Today's panchang", "Tithi today" |
| `ask_astrologer` | General questions | "What is Saturn return?" |

### Travel Domain

| Intent | Description | Example Queries |
|--------|-------------|-----------------|
| `pnr_status` | PNR status | "PNR 1234567890" |
| `train_status` | Train running status | "Train 12301 status" |
| `metro_ticket` | Metro route/fare | "Metro from Dwarka to Rajiv Chowk" |

### Utility Domain

| Intent | Description | Example Queries |
|--------|-------------|-----------------|
| `weather` | Weather info | "Weather in Mumbai" |
| `get_news` | News headlines | "Latest news", "Tech news" |
| `local_search` | Nearby places | "Restaurants near me" |
| `image` | Generate image | "Generate image of sunset" |
| `set_reminder` | Set reminder | "Remind me in 5 minutes" |
| `subscription` | Manage subscriptions | "Subscribe horoscope aries" |

### Game Domain

| Intent | Description | Example Queries |
|--------|-------------|-----------------|
| `word_game` | Word games | "Play word game" |

### Conversation Domain

| Intent | Description | Example Queries |
|--------|-------------|-----------------|
| `chat` | General chat | "Hello", "What can you do?" |

---

## LangGraph State

### BotState (bot/state.py)

```python
from typing import TypedDict, Optional, List, Dict, Any

class WhatsAppMessage(TypedDict):
    message_id: str
    from_number: str
    phone_number_id: str
    timestamp: str
    message_type: str  # "text", "image", "audio"
    text: Optional[str]
    media_id: Optional[str]

class BotState(TypedDict):
    # Input
    whatsapp_message: WhatsAppMessage
    current_query: str
    user_phone: str

    # Processing
    intent: str
    domain: str
    extracted_entities: Dict[str, Any]
    conversation_context: List[Dict]

    # Astrology specific
    birth_details: Optional[Dict]
    zodiac_sign: Optional[str]

    # Output
    response_text: Optional[str]
    response_type: str  # "text", "image"
    response_media_url: Optional[str]

    # Control
    should_fallback: bool
    error: Optional[str]
    tool_result: Optional[Dict]
```

---

## Graph Routing (bot/graph.py)

### Route Function

```python
def route_by_intent(state: BotState) -> str:
    intent = state.get("intent", "chat")

    intent_to_node = {
        # Astrology
        "get_horoscope": "get_horoscope",
        "birth_chart": "birth_chart",
        "kundli_matching": "kundli_matching",
        "dosha_check": "dosha_check",
        "life_prediction": "life_prediction",
        "numerology": "numerology",
        "tarot_reading": "tarot_reading",
        "get_panchang": "get_panchang",
        "ask_astrologer": "ask_astrologer",

        # Travel
        "pnr_status": "pnr_status",
        "train_status": "train_status",
        "metro_ticket": "metro_ticket",

        # Utility
        "weather": "weather",
        "get_news": "get_news",
        "local_search": "local_search",
        "image": "image_gen",
        "set_reminder": "set_reminder",
        "subscription": "subscription",

        # Game
        "word_game": "word_game",

        # Default
        "chat": "chat",
        "unknown": "chat",
    }

    return intent_to_node.get(intent, "chat")
```

### Graph Structure

```
START → intent_detection → [conditional routing] → handler_node → [fallback check] → END
                                                                          ↓
                                                                      fallback → END
```

---

## Node Handler Template

```python
"""
Node Handler Template

Each node follows this pattern:
1. Extract data from state
2. Validate inputs
3. Call tool/API
4. Format response
5. Return state updates
"""

import logging
from bot.state import BotState
from bot.utils.response_formatter import create_error_response

logger = logging.getLogger(__name__)
INTENT = "your_intent"


async def handle_your_feature(state: BotState) -> dict:
    """
    Handle your feature requests.

    Args:
        state: Current bot state

    Returns:
        State updates dict
    """
    query = state.get("current_query", "")
    entities = state.get("extracted_entities", {})
    phone = state.get("user_phone", "")

    try:
        # 1. Validate inputs
        if not some_required_field:
            return {
                "response_text": "Please provide X",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        # 2. Call tool/API
        result = await your_tool_function(params)

        # 3. Handle errors
        if not result.get("success"):
            return create_error_response(
                error_msg="Could not process request",
                intent=INTENT,
                feature_name="Your Feature"
            )

        # 4. Format response
        response = format_response(result["data"])

        return {
            "response_text": response,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "tool_result": result,
        }

    except Exception as e:
        logger.error(f"Error in your_feature: {e}", exc_info=True)
        return create_error_response(
            error_msg="Something went wrong",
            intent=INTENT,
            feature_name="Your Feature",
            raw_error=str(e)
        )
```

---

## Services

### Subscription Service (bot/services/subscription_service.py)

```python
from enum import Enum

class SubscriptionType(Enum):
    DAILY_HOROSCOPE = "daily_horoscope"
    TRANSIT_ALERTS = "transit_alerts"
    WEEKLY_HOROSCOPE = "weekly_horoscope"
    MONTHLY_HOROSCOPE = "monthly_horoscope"

class SubscriptionService:
    async def subscribe(
        phone: str,
        subscription_type: SubscriptionType,
        zodiac_sign: str = None,
        preferred_time: str = "07:00"
    ) -> dict

    async def unsubscribe(
        phone: str,
        subscription_type: SubscriptionType
    ) -> dict

    async def is_subscribed(
        phone: str,
        subscription_type: SubscriptionType
    ) -> bool

    async def get_user_subscriptions(phone: str) -> List[Subscription]

    async def get_due_subscribers(
        subscription_type: SubscriptionType,
        target_time: str
    ) -> List[Subscription]
```

### Horoscope Scheduler (bot/services/horoscope_scheduler.py)

```python
class HoroscopeScheduler:
    async def start()      # Start background scheduler
    async def stop()       # Stop scheduler

    # Runs every minute, checks for due subscribers
    async def _scheduler_loop()

    # Send horoscope to subscriber
    async def _send_horoscope(subscription: Subscription)

    # Manual trigger for testing
    async def send_test_horoscope(phone: str, zodiac_sign: str)
```

### Transit Service (bot/services/transit_service.py)

```python
class TransitEventType(Enum):
    SIGN_CHANGE = "sign_change"
    HOUSE_TRANSIT = "house_transit"
    RETROGRADE_START = "retrograde_start"
    RETROGRADE_END = "retrograde_end"
    CONJUNCTION = "conjunction"
    ASPECT = "aspect"

class TransitService:
    async def start()
    async def stop()

    async def get_upcoming_transits(days: int = 30) -> List[TransitEvent]
    async def get_personalized_transits(phone: str) -> dict
    def is_planet_retrograde(planet: str) -> bool
```

---

## API Endpoints

### Health Check

```
GET /
Response: {"status": "healthy", "service": "D23Bot", "version": "2.0.0"}

GET /health
Response: {"status": "healthy", "lite_mode": false}
```

### WhatsApp Webhook

```
GET /webhook
Query Params: hub.mode, hub.verify_token, hub.challenge
Response: hub.challenge (for verification)

POST /webhook
Headers: X-Hub-Signature-256
Body: WhatsApp webhook payload
Response: {"status": "ok"}
```

---

## Internationalization (i18n)

### Supported Languages (22)

```python
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "te": "Telugu",
    "mr": "Marathi",
    "ta": "Tamil",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "mai": "Maithili",
    "sa": "Sanskrit",
    "ks": "Kashmiri",
    "ne": "Nepali",
    "sd": "Sindhi",
    "kok": "Konkani",
    "doi": "Dogri",
    "mni": "Manipuri",
    "sat": "Santali",
    "ur": "Urdu",
}
```

### Translation Usage

```python
from bot.i18n import get_translator

translator = get_translator()

# Detect language from text
lang = translator.detect_language("नमस्ते")  # Returns "hi"

# Translate response
response = translator.translate(
    template="horoscope_daily",
    lang="hi",
    zodiac=zodiac_sign,
    prediction=prediction
)

# Get zodiac name in language
name = translator.get_zodiac_name("aries", "hi")  # Returns "मेष"
```

---

## Error Handling

### Response Formatter (bot/utils/response_formatter.py)

```python
def sanitize_error(error: str, context: str = "") -> str:
    """Convert technical errors to user-friendly messages."""

    error_patterns = {
        "timeout": "The service is taking too long. Please try again.",
        "connection": "Unable to connect to the service.",
        "rate limit": "Too many requests. Please wait a moment.",
        "api": "External service is temporarily unavailable.",
        "validation": "Please check your input and try again.",
    }
    # ... maps technical errors to friendly messages

def create_error_response(
    error_msg: str,
    intent: str,
    context: str = "",
    suggestions: List[str] = None,
    example: str = None,
    should_fallback: bool = False,
    raw_error: str = None
) -> dict:
    """Create standardized error response."""

def create_missing_input_response(
    missing_fields: List[str],
    intent: str,
    feature_name: str,
    example: str = None
) -> dict:
    """Create response for missing required inputs."""

def create_service_error_response(
    intent: str,
    feature_name: str,
    raw_error: str = None,
    retry_suggestion: bool = True
) -> dict:
    """Create response for service/API errors."""
```

---

## Testing

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run pytest
pytest -v

# Run with coverage
pytest --cov=bot --cov-report=html

# Run specific test file
pytest tests/test_subscription.py -v

# Run by marker
pytest -m "unit" -v
pytest -m "not slow" -v
```

### Quick Tests

```bash
# Subscription feature tests (no DB required)
python test_subscription_quick.py

# Logic validation
python test_bot_logic.py --quick

# Test specific domain
python test_bot_logic.py --domain astrology
python test_bot_logic.py --domain subscription
```

### Test Markers

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.slow          # Slow tests
```

---

## Running the Application

### Development (LITE_MODE)

```bash
# No database required
LITE_MODE=true python main.py
```

### Production

```bash
# With PostgreSQL
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 9002 --workers 4
```

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9002"]
```

```bash
docker build -t d23bot .
docker run -p 9002:9002 --env-file .env d23bot
```

---

## Adding New Features

### 1. Add Intent Pattern (bot/constants/intents.py)

```python
UTILITY_INTENT_PATTERNS["your_feature"] = [
    r"your.*pattern",
    r"another.*pattern",
]
```

### 2. Create Node Handler (bot/nodes/your_feature.py)

```python
async def handle_your_feature(state: BotState) -> dict:
    # Implementation
    pass
```

### 3. Create Tool (bot/tools/your_tool.py)

```python
async def your_api_call(params):
    # API integration
    pass
```

### 4. Register in Graph (bot/graph.py)

```python
# Import
from bot.nodes.your_feature import handle_your_feature

# Add to route_by_intent
"your_feature": "your_feature",

# Add node
graph.add_node("your_feature", handle_your_feature)

# Add to conditional edges
"your_feature": "your_feature",

# Add to fallback list
for node in [..., "your_feature", ...]:
```

---

## Security

### Implemented

1. **Webhook Signature Verification** (HMAC-SHA256)
   ```python
   # bot/whatsapp/signature.py
   def verify_signature(payload: bytes, signature: str) -> bool
   ```

2. **Rate Limiting**
   ```python
   # bot/utils/rate_limiter.py
   rate_limiter = RateLimiter(requests_per_minute=30)
   ```

3. **Input Validation**
   ```python
   # bot/utils/validators.py
   validate_phone_number(phone)
   validate_date(date_str)
   sanitize_input(text)
   ```

4. **SQL Injection Prevention**
   - Parameterized queries in all database operations

5. **Error Sanitization**
   - Technical errors never exposed to users

---

## Monitoring & Logging

### Log Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)s)'
)
```

### Key Log Points

- Webhook received: `INFO`
- Intent detected: `INFO`
- API calls: `DEBUG`
- Errors: `ERROR` with traceback
- Subscription events: `INFO`

---

## Common Issues & Solutions

### 1. "Module not found" errors
```bash
# Ensure you're in virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Database connection errors
```bash
# Check PostgreSQL is running
# Or use LITE_MODE=true for development
```

### 3. WhatsApp webhook not receiving
- Verify ngrok is running
- Check webhook URL in Meta Developer Console
- Verify WEBHOOK_VERIFY_TOKEN matches

### 4. Rate limiting
- Default: 30 requests/minute per user
- Adjust in `bot/utils/rate_limiter.py`

---

## Quick Reference Commands

```bash
# Start server
LITE_MODE=true python main.py

# Run tests
pytest -v

# Quick subscription test
python test_subscription_quick.py

# Logic validation
python test_bot_logic.py --quick

# Test specific feature
python test_bot_logic.py --domain subscription

# Generate coverage report
pytest --cov=bot --cov-report=html
```

---

## Contact & Support

For issues and contributions, refer to the repository documentation.

---

*Last Updated: December 2024*
