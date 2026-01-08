# Unified Platform

A modular, loosely-coupled codebase combining WhatsApp Bot and OhGrt API functionality.

## Architecture

```
unified_platform/
├── common/                 # Shared code (can be used by both modules)
│   ├── config/            # Base configuration
│   ├── models/            # Shared Pydantic models
│   ├── llm/               # LLM clients (OpenAI, Ollama)
│   ├── services/          # Shared services (weather, news, image)
│   ├── whatsapp/          # WhatsApp client
│   ├── database/          # Database utilities
│   ├── graph/             # Common LangGraph components
│   ├── i18n/              # Internationalization
│   └── utils/             # Utility functions
│
├── whatsapp_bot/          # WhatsApp Bot module (independent)
│   ├── config.py          # Bot-specific configuration
│   ├── main.py            # FastAPI entry point
│   ├── graph/             # Bot-specific LangGraph
│   │   └── nodes/         # PNR, trains, astrology, etc.
│   ├── services/          # Subscriptions, reminders
│   └── webhook/           # WhatsApp webhook handlers
│
├── ohgrt_api/             # OhGrt API module (independent)
│   ├── config.py          # API-specific configuration
│   ├── main.py            # FastAPI entry point
│   ├── auth/              # Authentication (Firebase, JWT)
│   ├── chat/              # Chat API endpoints
│   ├── middleware/        # Security, rate limiting, metrics
│   └── oauth/             # OAuth integrations
│
├── run_bot.py             # Entry point for WhatsApp Bot
├── run_api.py             # Entry point for OhGrt API
├── requirements.txt       # Common dependencies
├── requirements-bot.txt   # Bot-specific dependencies
└── requirements-api.txt   # API-specific dependencies
```

## Key Principles

1. **Loose Coupling**: Each module can be developed, deployed, and scaled independently
2. **Shared Common Code**: Reusable components in `common/` reduce duplication
3. **Independent Configuration**: Each module has its own config extending base settings
4. **Modular Entry Points**: Separate entry points for each application

## Quick Start

### 1. Setup

```bash
cd unified_platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt  # Common
pip install -r requirements-bot.txt  # For WhatsApp Bot
pip install -r requirements-api.txt  # For OhGrt API
```

### 2. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
```

### 3. Run WhatsApp Bot

```bash
python run_bot.py
# or
uvicorn whatsapp_bot.main:app --reload --port 9002
```

### 4. Run OhGrt API

```bash
python run_api.py
# or
uvicorn ohgrt_api.main:app --reload --port 9002
```

## Development

### Adding a New Feature to WhatsApp Bot

1. Create a new node in `whatsapp_bot/graph/nodes/`
2. Add intent patterns to the graph
3. Register the node in `whatsapp_bot/graph/graph.py`

### Adding a New Feature to OhGrt API

1. Create a new router in `ohgrt_api/`
2. Add service logic
3. Include router in `ohgrt_api/main.py`

### Adding Shared Functionality

1. Add to `common/` module
2. Import in both `whatsapp_bot` and `ohgrt_api` as needed

## Testing

```bash
# Run all tests
pytest

# Run specific module tests
pytest whatsapp_bot/tests/
pytest ohgrt_api/tests/
```

## Docker

```bash
# Build WhatsApp Bot
docker build -f Dockerfile.bot -t whatsapp-bot .

# Build OhGrt API
docker build -f Dockerfile.api -t ohgrt-api .

# Or use docker-compose
docker-compose up
```

## Environment Variables

See `.env.example` for all available configuration options.

### Required for WhatsApp Bot
- `OPENAI_API_KEY`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`

### Required for OhGrt API
- `OPENAI_API_KEY`
- `JWT_SECRET_KEY`
- `FIREBASE_CREDENTIALS_PATH` (for Google auth)

## License

Proprietary - All rights reserved.
