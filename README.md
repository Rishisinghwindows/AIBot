# Puch - Multi-Platform AI Assistant

A unified AI assistant platform serving WhatsApp, iOS, and Web users with astrology, travel, weather, news, image generation, and conversational AI capabilities. Supports 22 Indian languages.

```
┌─────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│   │ WhatsApp │    │   iOS    │    │   Web    │                 │
│   │   Bot    │    │   App    │    │  D23Web  │                 │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘                 │
│        │               │               │                        │
│        └───────────────┼───────────────┘                        │
│                        ▼                                        │
│              ┌─────────────────┐                                │
│              │    OhGrtApi     │                                │
│              │  (FastAPI Hub)  │                                │
│              └────────┬────────┘                                │
│                       │                                         │
│        ┌──────────────┼──────────────┐                         │
│        ▼              ▼              ▼                          │
│   ┌─────────┐   ┌──────────┐   ┌──────────┐                    │
│   │LangGraph│   │ Services │   │PostgreSQL│                    │
│   │Workflow │   │  Layer   │   │ Database │                    │
│   └─────────┘   └──────────┘   └──────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Projects

| Project | Description | Stack |
|---------|-------------|-------|
| **OhGrtApi** | Unified backend API | FastAPI, LangGraph, PostgreSQL |
| **OhGrtApp** | iOS mobile app | SwiftUI, StoreKit |
| **D23Web** | Web landing & chat | Next.js 15, TypeScript |
| **D23Bot** | Legacy WhatsApp bot | Python, LangGraph (migrated) |

## Features Matrix

| Feature | WhatsApp | iOS | Web |
|---------|----------|-----|-----|
| Chat/Conversation | ✅ | ✅ | ✅ |
| Horoscope | ✅ | ✅ | ✅ |
| Birth Chart/Kundli | ✅ | ✅ | ✅ |
| Numerology | ✅ | ✅ | ✅ |
| Tarot Reading | ✅ | ✅ | ✅ |
| Panchang | ✅ | ✅ | ✅ |
| Dosha Analysis | ✅ | ✅ | ✅ |
| Kundli Matching | ✅ | ✅ | ✅ |
| Life Prediction | ✅ | ✅ | ✅ |
| PNR Status | ✅ | ✅ | ✅ |
| Train Status | ✅ | ✅ | ✅ |
| Weather | ✅ | ✅ | ✅ |
| News | ✅ | ✅ | ✅ |
| Image Generation | ✅ | ✅ | ✅ |
| Word Games | ✅ | ❌ | ✅ |
| Reminders | ✅ | ❌ | ❌ |
| Multi-language (22) | ✅ | ✅ | ✅ |
| Subscriptions | ✅ | ✅ | ❌ |

---

## Project Structure

```
puch/
├── OhGrtApi/              # Backend API (FastAPI)
│   ├── app/
│   │   ├── main.py        # Application entry point
│   │   ├── config.py      # Environment configuration
│   │   ├── auth/          # JWT authentication
│   │   ├── db/            # Database models & connection
│   │   ├── chat/          # Chat endpoints (iOS)
│   │   ├── web/           # Web anonymous chat
│   │   ├── whatsapp/      # WhatsApp webhook
│   │   ├── graph/         # LangGraph workflow
│   │   │   ├── whatsapp_graph.py
│   │   │   ├── state.py
│   │   │   └── nodes/     # Intent handlers
│   │   ├── services/      # Business logic
│   │   ├── i18n/          # Multi-language support
│   │   ├── astro/         # Astrology engine
│   │   └── middleware/    # Security, rate limiting
│   ├── requirements.txt
│   └── .env.example
│
├── OhGrtApp/              # iOS App (SwiftUI)
│   ├── OhGrt/
│   │   ├── Features/
│   │   │   ├── Chat/      # Chat interface
│   │   │   ├── Profile/   # User profile
│   │   │   └── Subscription/
│   │   ├── Core/
│   │   │   ├── Network/   # API client
│   │   │   └── Usage/     # Usage tracking
│   │   └── Models/        # Data models
│   └── OhGrt.xcodeproj
│
├── D23Web/                # Web App (Next.js)
│   ├── app/
│   │   ├── page.tsx       # Landing page
│   │   ├── chat/          # Chat page
│   │   └── layout.tsx
│   ├── components/
│   │   ├── chat/          # Chat components
│   │   ├── ui/            # UI primitives
│   │   └── header.tsx
│   ├── lib/
│   │   ├── api-client.ts  # API integration
│   │   └── utils.ts
│   └── package.json
│
└── D23Bot/                # Legacy bot (deprecated)
    └── bot/               # Migrated to OhGrtApi
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 14+
- Xcode 15+ (for iOS)

### 1. OhGrtApi Setup

```bash
cd OhGrtApi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Run database migrations (if using Alembic)
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 9002
```

### 2. D23Web Setup

```bash
cd D23Web

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:9002" > .env.local

# Start development server
npm run dev
```

### 3. OhGrtApp Setup

```bash
cd OhGrtApp

# Open in Xcode
open OhGrt.xcodeproj

# Update API URL in Core/Network/APIConfig.swift
# Run on simulator or device
```

---

## Environment Variables

### OhGrtApi (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ohgrt

# Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=sk-...

# WhatsApp Cloud API (Meta Business)
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789
WHATSAPP_VERIFY_TOKEN=your-webhook-verify-token
WHATSAPP_APP_SECRET=your-app-secret

# Image Generation (fal.ai)
FAL_KEY=fal-...

# Travel (Railway API)
RAILWAY_API_KEY=your-railway-api-key

# News
NEWS_API_KEY=your-news-api-key

# Weather
OPENWEATHER_API_KEY=your-openweather-key

# LangSmith (optional, for tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=ohgrt
```

### D23Web (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:9002
```

---

## API Reference

### Authentication Endpoints

```bash
# Register new user (iOS)
POST /auth/register
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "User Name"
}

# Login
POST /auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}
# Returns: { "access_token": "...", "token_type": "bearer" }

# Get current user
GET /auth/me
Authorization: Bearer <token>
```

### Chat Endpoints (iOS - Authenticated)

```bash
# Send message
POST /chat/send
Authorization: Bearer <token>
{
  "message": "What's my horoscope?",
  "language": "en"
}

# Get chat history
GET /chat/history?limit=50
Authorization: Bearer <token>

# Clear chat
DELETE /chat/clear
Authorization: Bearer <token>
```

### Web Chat Endpoints (Anonymous)

```bash
# Create session
POST /web/session
# Returns: { "session_id": "uuid", "created_at": "...", "language": "en" }

# Send message
POST /web/chat
{
  "session_id": "uuid",
  "message": "Weather in Delhi",
  "language": "en"
}

# Get chat history
GET /web/chat/history/{session_id}?limit=50
```

### WhatsApp Webhook

```bash
# Webhook verification (Meta)
GET /whatsapp/webhook?hub.mode=subscribe&hub.verify_token=xxx&hub.challenge=yyy

# Message webhook
POST /whatsapp/webhook
# Receives Meta webhook payload
```

### Astrology Endpoints

```bash
# Get horoscope
POST /astrology/horoscope
{
  "zodiac_sign": "aries",
  "period": "daily"  # daily, weekly, monthly
}

# Calculate birth chart
POST /astrology/birth-chart
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "birth_place": "Mumbai, India",
  "name": "User Name"
}

# Get numerology
POST /astrology/numerology
{
  "birth_date": "1990-05-15",
  "name": "User Name"
}

# Tarot reading
POST /astrology/tarot
{
  "question": "What does my career hold?",
  "spread_type": "three_card"
}

# Panchang
POST /astrology/panchang
{
  "date": "2025-01-15",
  "location": "Delhi, India"
}

# Dosha analysis
POST /astrology/dosha
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "birth_place": "Mumbai, India"
}

# Kundli matching
POST /astrology/kundli-matching
{
  "person1": {
    "birth_date": "1990-05-15",
    "birth_time": "14:30",
    "birth_place": "Mumbai, India"
  },
  "person2": {
    "birth_date": "1992-08-20",
    "birth_time": "10:00",
    "birth_place": "Delhi, India"
  }
}
```

### Travel Endpoints

```bash
# PNR Status
POST /travel/pnr
{
  "pnr_number": "1234567890"
}

# Train status
POST /travel/train-status
{
  "train_number": "12301",
  "date": "2025-01-15"
}
```

### Weather Endpoint

```bash
POST /weather
{
  "location": "Delhi, India"
}
```

### News Endpoint

```bash
GET /news?category=technology&country=in&limit=10
```

### Image Generation

```bash
POST /image/generate
{
  "prompt": "Beautiful sunset over mountains",
  "style": "realistic"  # realistic, artistic, anime
}
```

---

## LangGraph Workflow

The message processing uses LangGraph for intent-based routing:

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   detect    │  Detect language & intent
│   intent    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│              ROUTER                      │
│  Routes based on detected intent         │
└────┬────┬────┬────┬────┬────┬────┬──────┘
     │    │    │    │    │    │    │
     ▼    ▼    ▼    ▼    ▼    ▼    ▼
   chat astro pnr train news weather image
     │    │    │    │    │    │    │
     └────┴────┴────┴────┴────┴────┘
                   │
                   ▼
            ┌─────────────┐
            │     END     │
            └─────────────┘
```

### Intent Types

| Intent | Triggers | Handler |
|--------|----------|---------|
| `horoscope` | "horoscope", "rashifal", zodiac names | astro_node |
| `birth_chart` | "birth chart", "kundli", "janam patri" | astro_node |
| `numerology` | "numerology", "lucky number" | astro_node |
| `tarot` | "tarot", "card reading" | astro_node |
| `panchang` | "panchang", "tithi", "muhurat" | astro_node |
| `dosha` | "dosha", "manglik" | astro_node |
| `kundli_match` | "kundli matching", "compatibility" | astro_node |
| `pnr_status` | "pnr", 10-digit number | travel_node |
| `train_status` | "train status", train number | travel_node |
| `weather` | "weather", "mausam", city names | weather_node |
| `news` | "news", "headlines", "samachar" | news_node |
| `image_gen` | "generate image", "create picture" | image_node |
| `word_game` | "word game", "antakshari" | game_node |
| `reminder` | "remind me", "set reminder" | reminder_node |
| `chat` | Default fallback | chat_node |

---

## Multi-Language Support

Supports 22 Indian languages with automatic detection:

| Language | Code | Script |
|----------|------|--------|
| Hindi | hi | Devanagari |
| Bengali | bn | Bengali |
| Telugu | te | Telugu |
| Marathi | mr | Devanagari |
| Tamil | ta | Tamil |
| Gujarati | gu | Gujarati |
| Kannada | kn | Kannada |
| Malayalam | ml | Malayalam |
| Odia | or | Odia |
| Punjabi | pa | Gurmukhi |
| Assamese | as | Assamese |
| Maithili | mai | Devanagari |
| Sanskrit | sa | Devanagari |
| Urdu | ur | Arabic |
| Sindhi | sd | Arabic |
| Nepali | ne | Devanagari |
| Konkani | kok | Devanagari |
| Dogri | doi | Devanagari |
| Kashmiri | ks | Arabic |
| Manipuri | mni | Meetei Mayek |
| Bodo | brx | Devanagari |
| Santali | sat | Ol Chiki |

Detection uses:
1. Script-based detection (Unicode ranges)
2. Keyword-based detection (language-specific words)
3. User preference from session

---

## Development Commands

### OhGrtApi

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 9002

# Run with specific host (for mobile testing)
uvicorn app.main:app --reload --host 0.0.0.0 --port 9002

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Type checking
mypy app/

# Linting
ruff check app/

# Format code
ruff format app/

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Generate requirements
pip freeze > requirements.txt
```

### D23Web

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Linting
npm run lint

# Type checking
npx tsc --noEmit
```

### OhGrtApp (iOS)

```bash
# Open project
open OhGrt.xcodeproj

# Build from command line
xcodebuild -scheme OhGrt -sdk iphonesimulator

# Run tests
xcodebuild test -scheme OhGrt -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 15'
```

---

## WhatsApp Integration Setup

### 1. Meta Business Setup

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app (Business type)
3. Add WhatsApp product
4. Get test phone number and access token

### 2. Webhook Configuration

Configure webhook URL:
```
URL: https://your-domain.com/whatsapp/webhook
Verify Token: your-verify-token (from .env)
```

Subscribe to webhook fields:
- `messages`
- `message_deliveries`
- `message_reads`

### 3. Test with ngrok (Development)

```bash
# Install ngrok
brew install ngrok

# Start tunnel
ngrok http 8000

# Use the HTTPS URL in Meta webhook settings
# Example: https://abc123.ngrok.io/whatsapp/webhook
```

---

## Deployment

### OhGrtApi (Railway/Render)

```bash
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### D23Web (Vercel)

```bash
# Deploy
vercel

# Production deploy
vercel --prod
```

### Environment Variables (Production)

Set all environment variables in your deployment platform's dashboard.

---

## Claude AI Integration

This project is designed to work with Claude AI for development. Here are useful commands and contexts:

### Working with Claude Code

```bash
# Start Claude Code in the project
cd /Users/pawansingh/Desktop/puch
claude

# Or specify working directories
claude --add-dir OhGrtApi --add-dir D23Web --add-dir OhGrtApp
```

### Useful Prompts for Claude

**Understanding the codebase:**
```
What is the architecture of the Puch project?
How does the LangGraph workflow process messages?
What astrology features are available?
```

**Adding new features:**
```
Add a new intent for [feature] to the LangGraph workflow
Create a new service for [functionality]
Add a new API endpoint for [purpose]
```

**Debugging:**
```
Why is the WhatsApp webhook not receiving messages?
Debug the astrology birth chart calculation
Fix the language detection for Tamil text
```

**Code review:**
```
Review the security of the authentication system
Check for potential issues in the web chat implementation
Optimize the database queries in chat history
```

### Project Context for Claude

When working with Claude, provide context:

```
This is a multi-platform AI assistant:
- OhGrtApi: FastAPI backend with LangGraph for intent routing
- D23Web: Next.js landing page with anonymous chat
- OhGrtApp: iOS app with authenticated chat
- Features: astrology, travel, weather, news, image generation
- 22 Indian language support
```

### Key Files to Reference

| File | Purpose |
|------|---------|
| `OhGrtApi/app/graph/whatsapp_graph.py` | Main message processing workflow |
| `OhGrtApi/app/graph/state.py` | State definitions for LangGraph |
| `OhGrtApi/app/graph/nodes/*.py` | Intent handlers |
| `OhGrtApi/app/services/*.py` | Business logic layer |
| `OhGrtApi/app/config.py` | Environment configuration |
| `D23Web/lib/api-client.ts` | Web API client |
| `OhGrtApp/OhGrt/Core/Network/` | iOS API client |

---

## Troubleshooting

### Common Issues

**WhatsApp webhook not working:**
1. Check WHATSAPP_VERIFY_TOKEN matches Meta config
2. Verify webhook URL is HTTPS
3. Check server logs for errors
4. Ensure all webhook fields are subscribed

**iOS app can't connect:**
1. Verify API URL in APIConfig.swift
2. Check JWT token is valid
3. Ensure API is running and accessible
4. Check for SSL certificate issues (use http:// for local)

**Web chat not working:**
1. Check NEXT_PUBLIC_API_URL in .env.local
2. Verify CORS settings in OhGrtApi
3. Check browser console for errors
4. Ensure API is running

**Language detection incorrect:**
1. Check input text encoding (UTF-8)
2. Verify i18n detector is imported correctly
3. Test with pure script text (no transliteration)

**Database connection issues:**
1. Verify DATABASE_URL is correct
2. Check PostgreSQL is running
3. Run migrations: `alembic upgrade head`
4. Check connection limits

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m 'Add my feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

Private - All rights reserved.

---

## Contact

- Website: [d23.ai](https://d23.ai)
- WhatsApp: [puch.ai/hi](https://puch.ai/hi)
- Email: support@d23.ai
