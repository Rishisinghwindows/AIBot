# Architecture Refactoring Plan

## Current Problems

### 1. Flat Graph Structure
```
Currently: 20+ nodes all at the same level
- Makes graph hard to visualize and debug
- Every new feature adds complexity to main graph
- No logical grouping
```

### 2. Intent Explosion
```
Every feature = new intent = new routing logic
- 25+ intents and growing
- Pattern matching in intent.py getting messy
- Hard to add new features without breaking existing ones
```

### 3. Session Management Gaps
```
Current: PostgresSaver with phone_number as thread_id
Missing:
- User profile persistence (birth details, preferences)
- Conversation context for multi-turn interactions
- Feature-specific state (ongoing kundli matching, etc.)
```

---

## Proposed Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                    MAIN ORCHESTRATOR                     │
│    (Intent Detection → Domain Classification)            │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   ASTROLOGY   │ │    TRAVEL     │ │   UTILITY     │
│   Sub-Graph   │ │   Sub-Graph   │ │   Sub-Graph   │
├───────────────┤ ├───────────────┤ ├───────────────┤
│ - Horoscope   │ │ - PNR Status  │ │ - Weather     │
│ - Kundli      │ │ - Train       │ │ - News        │
│ - Matching    │ │ - Metro       │ │ - Image Gen   │
│ - Dosha       │ └───────────────┘ │ - Local Search│
│ - Prediction  │                   │ - Reminder    │
│ - Panchang    │                   │ - Word Game   │
│ - Numerology  │                   │ - RAG Query   │
│ - Tarot       │                   └───────────────┘
└───────────────┘
```

### Domain Classification (First-Level Routing)

```python
# Instead of 25+ intents, use 4-5 domain categories
DomainType = Literal[
    "astrology",    # All astro features
    "travel",       # PNR, train, metro
    "utility",      # Weather, news, search, image
    "game",         # Word game, quizzes
    "conversation", # General chat, fallback
]
```

---

## Implementation Plan

### Phase 1: Create Sub-Graphs

#### A. Astrology Sub-Graph (`bot/graphs/astro_graph.py`)

```python
from langgraph.graph import StateGraph, START, END

def create_astro_graph() -> StateGraph:
    """Astrology domain sub-graph."""
    graph = StateGraph(AstroState)

    # Astro-specific intent detection
    graph.add_node("astro_intent", detect_astro_intent)

    # Feature nodes
    graph.add_node("horoscope", handle_horoscope)
    graph.add_node("birth_chart", handle_birth_chart)
    graph.add_node("kundli_matching", handle_kundli_matching)
    graph.add_node("dosha_check", handle_dosha_check)
    graph.add_node("life_prediction", handle_life_prediction)
    graph.add_node("panchang", handle_panchang)
    graph.add_node("numerology", handle_numerology)
    graph.add_node("tarot", handle_tarot)
    graph.add_node("ask_astrologer", handle_ask_astrologer)

    # Routing
    graph.add_edge(START, "astro_intent")
    graph.add_conditional_edges(
        "astro_intent",
        route_astro_intent,
        {
            "horoscope": "horoscope",
            "birth_chart": "birth_chart",
            # ... etc
        }
    )

    return graph


# Astro-specific state (extends base state)
class AstroState(TypedDict):
    # Base fields
    query: str
    user_phone: str

    # Astro-specific
    astro_intent: str  # horoscope, kundli, dosha, etc.
    birth_details: Optional[dict]  # {date, time, place}
    user_sign: Optional[str]
    chart_data: Optional[dict]
```

#### B. Travel Sub-Graph (`bot/graphs/travel_graph.py`)

```python
def create_travel_graph() -> StateGraph:
    """Travel domain sub-graph."""
    graph = StateGraph(TravelState)

    graph.add_node("travel_intent", detect_travel_intent)
    graph.add_node("pnr_status", handle_pnr_status)
    graph.add_node("train_status", handle_train_status)
    graph.add_node("metro_info", handle_metro_ticket)

    # Routing
    graph.add_edge(START, "travel_intent")
    graph.add_conditional_edges(...)

    return graph
```

#### C. Utility Sub-Graph (`bot/graphs/utility_graph.py`)

```python
def create_utility_graph() -> StateGraph:
    """Utility services sub-graph."""
    graph = StateGraph(UtilityState)

    graph.add_node("utility_intent", detect_utility_intent)
    graph.add_node("weather", handle_weather)
    graph.add_node("news", handle_news)
    graph.add_node("local_search", handle_local_search)
    graph.add_node("image_gen", handle_image_generation)
    graph.add_node("reminder", handle_reminder)
    graph.add_node("rag_query", handle_db_query)

    return graph
```

### Phase 2: Main Orchestrator

```python
# bot/graphs/main_graph.py

from langgraph.graph import StateGraph, START, END
from bot.graphs.astro_graph import create_astro_graph
from bot.graphs.travel_graph import create_travel_graph
from bot.graphs.utility_graph import create_utility_graph

def create_main_graph() -> StateGraph:
    """Main orchestrator graph with sub-graphs."""
    graph = StateGraph(BotState)

    # Domain classifier
    graph.add_node("classify_domain", classify_domain)

    # Sub-graphs as nodes
    astro_graph = create_astro_graph().compile()
    travel_graph = create_travel_graph().compile()
    utility_graph = create_utility_graph().compile()

    graph.add_node("astrology", astro_graph)
    graph.add_node("travel", travel_graph)
    graph.add_node("utility", utility_graph)
    graph.add_node("chat", handle_chat)
    graph.add_node("game", handle_word_game)

    # Routing
    graph.add_edge(START, "classify_domain")
    graph.add_conditional_edges(
        "classify_domain",
        route_to_domain,
        {
            "astrology": "astrology",
            "travel": "travel",
            "utility": "utility",
            "game": "game",
            "conversation": "chat",
        }
    )

    return graph
```

---

## Session Management Enhancement

### Current Implementation
```python
# Uses PostgresSaver with phone number as thread_id
thread_id = whatsapp_message.get("from_number", "default_thread")
config = {"configurable": {"thread_id": thread_id}}
```

### Proposed Enhancement

#### 1. User Profile Store (`bot/stores/user_store.py`)

```python
from typing import Optional
from datetime import datetime
import asyncpg

class UserProfile:
    """Persistent user profile for personalized predictions."""

    phone_number: str
    name: Optional[str]
    birth_date: Optional[str]
    birth_time: Optional[str]
    birth_place: Optional[str]
    moon_sign: Optional[str]
    sun_sign: Optional[str]
    ascendant: Optional[str]
    preferences: dict  # {language, notification_time, etc.}
    created_at: datetime
    updated_at: datetime


class UserStore:
    """Async user profile storage."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool

    async def get_user(self, phone: str) -> Optional[UserProfile]:
        """Get user profile by phone number."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE phone_number = $1",
                phone
            )
            return UserProfile(**row) if row else None

    async def save_birth_details(
        self,
        phone: str,
        birth_date: str,
        birth_time: str,
        birth_place: str
    ):
        """Save user's birth details for future use."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_profiles (phone_number, birth_date, birth_time, birth_place, updated_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (phone_number) DO UPDATE
                SET birth_date = $2, birth_time = $3, birth_place = $4, updated_at = NOW()
            """, phone, birth_date, birth_time, birth_place)

    async def get_birth_details(self, phone: str) -> Optional[dict]:
        """Get saved birth details."""
        user = await self.get_user(phone)
        if user and user.birth_date:
            return {
                "birth_date": user.birth_date,
                "birth_time": user.birth_time,
                "birth_place": user.birth_place,
            }
        return None
```

#### 2. Database Schema

```sql
-- User profiles for personalized predictions
CREATE TABLE user_profiles (
    phone_number VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    birth_date DATE,
    birth_time TIME,
    birth_place VARCHAR(100),

    -- Calculated from birth chart (cached)
    moon_sign VARCHAR(20),
    sun_sign VARCHAR(20),
    ascendant VARCHAR(20),
    moon_nakshatra VARCHAR(30),

    -- Preferences
    preferred_language VARCHAR(10) DEFAULT 'en',
    notification_enabled BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Conversation context for multi-turn flows
CREATE TABLE conversation_context (
    phone_number VARCHAR(20),
    context_type VARCHAR(50),  -- 'kundli_matching', 'prediction', etc.
    context_data JSONB,
    expires_at TIMESTAMP,
    PRIMARY KEY (phone_number, context_type)
);

-- Query history for analytics
CREATE TABLE query_history (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20),
    query_text TEXT,
    intent VARCHAR(50),
    domain VARCHAR(20),
    response_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. Context-Aware Astrology Nodes

```python
# bot/nodes/astro_node_v2.py

async def handle_life_prediction_v2(state: BotState) -> dict:
    """Enhanced life prediction with user profile lookup."""
    phone = state["whatsapp_message"]["from_number"]
    entities = state.get("extracted_entities", {})

    # Try to get birth details from entities first
    birth_date = entities.get("birth_date", "").strip()
    birth_time = entities.get("birth_time", "").strip()
    birth_place = entities.get("birth_place", "").strip()

    # If missing, check user profile
    if not all([birth_date, birth_time, birth_place]):
        user_store = get_user_store()
        saved = await user_store.get_birth_details(phone)

        if saved:
            birth_date = birth_date or saved["birth_date"]
            birth_time = birth_time or saved["birth_time"]
            birth_place = birth_place or saved["birth_place"]

    # If still missing, ask user (offer to save)
    if not all([birth_date, birth_time, birth_place]):
        return {
            "response_text": (
                "*Life Prediction*\n\n"
                "I need your birth details. Please share:\n"
                "- Date of birth (DD-MM-YYYY)\n"
                "- Time of birth (HH:MM AM/PM)\n"
                "- Place of birth\n\n"
                "*Example:* 15-08-1990, 10:30 AM, Delhi\n\n"
                "_I'll save your details for future readings!_"
            ),
            "should_fallback": False,
        }

    # Save birth details for future use
    user_store = get_user_store()
    await user_store.save_birth_details(phone, birth_date, birth_time, birth_place)

    # Continue with prediction...
    result = await get_life_prediction(birth_date, birth_time, birth_place, ...)
    return format_response(result)
```

---

## Comparison: How Others Handle This

### 1. LangChain Multi-Agent Architecture
```
Supervisor Agent → Routes to specialized agents
- Each agent has its own tools
- Agents can call each other
- Central memory/state management
```

### 2. OpenAI Assistants API
```
Single Assistant with categorized tools
- Tools grouped by function
- Threads for conversation history
- Runs for execution state
```

### 3. Rasa Open Source
```
Stories + Forms for multi-turn
- Slots for entity persistence
- Custom actions for business logic
- Tracker for conversation state
```

### 4. Google Dialogflow CX
```
Flows + Pages architecture
- Each flow = domain (like our sub-graphs)
- Pages = conversation states
- Session parameters for context
```

---

## Migration Steps

### Step 1: Create Directory Structure
```
bot/
├── graphs/
│   ├── __init__.py
│   ├── main_graph.py       # Orchestrator
│   ├── astro_graph.py      # Astrology sub-graph
│   ├── travel_graph.py     # Travel sub-graph
│   └── utility_graph.py    # Utility sub-graph
├── stores/
│   ├── __init__.py
│   └── user_store.py       # User profile persistence
├── nodes/
│   ├── domain_classifier.py # Domain classification
│   └── ... (existing nodes)
└── state.py                 # Enhanced state definitions
```

### Step 2: Create Domain Classifier
```python
# Simple keyword-based domain classification
DOMAIN_KEYWORDS = {
    "astrology": [
        "horoscope", "kundli", "rashifal", "zodiac", "astrology",
        "manglik", "dosha", "prediction", "marriage", "career",
        "numerology", "tarot", "panchang", "muhurat", "gemstone"
    ],
    "travel": [
        "pnr", "train", "metro", "railway", "ticket", "status"
    ],
    "utility": [
        "weather", "news", "search", "image", "generate", "remind"
    ],
    "game": [
        "game", "play", "word", "quiz"
    ]
}
```

### Step 3: Implement Sub-Graphs
- Extract astrology nodes into astro_graph
- Extract travel nodes into travel_graph
- Extract utility nodes into utility_graph

### Step 4: Update Main Graph
- Replace flat structure with domain routing
- Use sub-graphs as nodes

### Step 5: Add User Store
- Create database tables
- Implement UserStore class
- Integrate with astrology nodes

---

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| Graph Nodes | 20+ flat nodes | 5 domain nodes + sub-graphs |
| Intent Types | 25+ intents | 5 domains + local intents |
| Code Organization | All in one file | Modular by domain |
| Debugging | Hard to trace | Domain isolation |
| Testing | Complex | Test sub-graphs independently |
| Adding Features | Risky | Add to relevant sub-graph |
| Session | Basic | User profiles + context |

---

## Implementation Priority

1. **High Priority**
   - User profile storage (birth details)
   - Domain classifier
   - Astrology sub-graph

2. **Medium Priority**
   - Travel sub-graph
   - Utility sub-graph
   - Context management

3. **Low Priority**
   - Query history
   - Analytics
   - Advanced personalization
