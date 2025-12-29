# Claude Code Context - D23Bot

> This file provides context for Claude Code to understand the D23Bot project.

## Project Summary

D23Bot is a WhatsApp chatbot for Vedic astrology with utility features. Built with:
- **FastAPI** - Web framework for webhook handling
- **LangGraph** - State machine for conversation flow
- **PostgreSQL** - Persistence (optional, has LITE_MODE)
- **OpenAI** - LLM for chat and predictions

## Key Entry Points

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, starts services |
| `bot/graph.py` | Main LangGraph workflow |
| `bot/whatsapp/webhook.py` | WhatsApp webhook handler |
| `bot/config.py` | Settings from environment |

## Architecture Pattern

```
WhatsApp → Webhook → LangGraph → Intent Detection → Node Handler → Response
```

## Adding Features Checklist

1. Add intent pattern: `bot/constants/intents.py`
2. Create node handler: `bot/nodes/<feature>.py`
3. Create tool (if needed): `bot/tools/<feature>_tool.py`
4. Register in graph: `bot/graph.py`
   - Import handler
   - Add to `route_by_intent()` mapping
   - Add node with `graph.add_node()`
   - Add to conditional edges
   - Add to fallback list

## Node Handler Pattern

```python
INTENT = "feature_name"

async def handle_feature(state: BotState) -> dict:
    query = state.get("current_query", "")
    entities = state.get("extracted_entities", {})

    # Process and return
    return {
        "response_text": "Response",
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }
```

## Important Directories

| Directory | Contents |
|-----------|----------|
| `bot/nodes/` | LangGraph node handlers (one per feature) |
| `bot/tools/` | External API integrations |
| `bot/services/` | Background services (schedulers) |
| `bot/stores/` | Data persistence layer |
| `bot/i18n/` | 22-language translation system |
| `bot/utils/` | Validators, formatters, rate limiting |
| `tests/` | Pytest test suite |

## State Schema (BotState)

Key fields:
- `current_query` - User's message text
- `user_phone` - User's phone number
- `intent` - Detected intent (e.g., "get_horoscope")
- `extracted_entities` - Parsed entities (dates, names, etc.)
- `response_text` - Response to send back
- `response_type` - "text" or "image"
- `should_fallback` - Whether to use fallback handler
- `error` - Error message if any

## Intent Categories

| Domain | Intents |
|--------|---------|
| Astrology | `get_horoscope`, `birth_chart`, `kundli_matching`, `dosha_check`, `life_prediction`, `numerology`, `tarot_reading`, `get_panchang`, `ask_astrologer` |
| Travel | `pnr_status`, `train_status`, `metro_ticket` |
| Utility | `weather`, `get_news`, `local_search`, `image`, `set_reminder`, `subscription` |
| Game | `word_game` |
| Default | `chat` |

## Services (Background Tasks)

| Service | Purpose | Start Function |
|---------|---------|----------------|
| HoroscopeScheduler | Daily horoscope delivery | `start_horoscope_scheduler()` |
| TransitService | Planetary transit alerts | `start_transit_service()` |
| ReminderService | User reminders | `ReminderService.start_scheduler()` |

Services are disabled when `LITE_MODE=true`.

## Testing Commands

```bash
# Quick test (no DB)
python test_subscription_quick.py

# Full pytest
pytest -v

# Test specific domain
python test_bot_logic.py --domain astrology

# With coverage
pytest --cov=bot --cov-report=html
```

## Environment Variables

Required:
- `OPENAI_API_KEY` - OpenAI API key
- `WHATSAPP_PHONE_ID` - WhatsApp Business phone ID
- `WHATSAPP_ACCESS_TOKEN` - WhatsApp API token

Optional:
- `LITE_MODE=true` - Skip database, use in-memory store
- `POSTGRES_*` - Database connection settings
- `WHATSAPP_APP_SECRET` - For webhook signature verification

## Common Tasks

### Run Development Server
```bash
LITE_MODE=true python main.py
```

### Add New Intent Pattern
Edit `bot/constants/intents.py`:
```python
UTILITY_INTENT_PATTERNS["new_feature"] = [
    r"pattern1",
    r"pattern2",
]
```

### Create Response with Error Handling
```python
from bot.utils.response_formatter import create_error_response

try:
    result = await api_call()
    return {"response_text": result, "intent": INTENT, ...}
except Exception as e:
    logger.error(f"Error: {e}")
    return create_error_response(
        error_msg="Friendly message",
        intent=INTENT,
        feature_name="Feature Name"
    )
```

### Test WhatsApp Locally
```bash
# 1. Start server
LITE_MODE=true python main.py

# 2. Start ngrok
ngrok http 9002

# 3. Configure webhook URL in Meta Developer Console
```

## File Naming Conventions

- Node handlers: `bot/nodes/<feature>.py` or `bot/nodes/<feature>_node.py`
- Tools: `bot/tools/<feature>_tool.py` or `bot/tools/<feature>_api.py`
- Tests: `tests/test_<feature>.py`

## Response Format

All node handlers must return:
```python
{
    "response_text": str,      # Required - message to user
    "response_type": str,      # Required - "text" or "image"
    "should_fallback": bool,   # Required - use fallback handler?
    "intent": str,             # Required - intent name
    "response_media_url": str, # Optional - for images
    "tool_result": dict,       # Optional - raw API result
    "error": str,              # Optional - error message
}
```

## Subscription System

Commands:
- `subscribe horoscope <sign>` - Daily horoscope
- `subscribe transit alerts` - Planetary alerts
- `my subscriptions` - View subscriptions
- `unsubscribe horoscope` - Stop horoscope
- `upcoming transits` - View transits

Files:
- `bot/services/subscription_service.py` - CRUD
- `bot/services/horoscope_scheduler.py` - Daily sender
- `bot/services/transit_service.py` - Transit alerts
- `bot/nodes/subscription_node.py` - Handler

## Zodiac Signs (English + Hindi)

```
aries/mesh, taurus/vrishabh, gemini/mithun, cancer/kark,
leo/singh, virgo/kanya, libra/tula, scorpio/vrishchik,
sagittarius/dhanu, capricorn/makar, aquarius/kumbh, pisces/meen
```

## Quick Debugging

```python
# Check intent detection
from bot.nodes.intent import detect_intent
state = {"current_query": "aries horoscope"}
result = detect_intent(state)
print(result["intent"])  # "get_horoscope"

# Check routing
from bot.graph import route_by_intent
state = {"intent": "subscription"}
print(route_by_intent(state))  # "subscription"
```
