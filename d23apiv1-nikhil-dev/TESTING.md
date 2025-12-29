# D23Bot Testing Guide

This guide covers all available testing methods for D23Bot.

## Quick Reference

| Method | Command | Use Case |
|--------|---------|----------|
| CLI Chat | `python cli_chat.py` | Manual interactive testing |
| Chainlit UI | `chainlit run chainlit_app.py` | Web-based testing |
| Pytest | `pytest` | Automated unit/integration tests |
| Logic Validation | `python test_bot_logic.py` | End-to-end intent testing |

---

## 1. CLI Chat Interface

A simple command-line interface for manual testing.

### Usage

```bash
# Basic usage (V1 graph)
python cli_chat.py

# Use V2 graph (domain-based routing)
python cli_chat.py --v2

# Run without database (limited features)
python cli_chat.py --no-db

# Enable debug mode
python cli_chat.py --debug
```

### Commands

| Command | Description |
|---------|-------------|
| `/quit`, `/exit` | Exit the chat |
| `/clear` | Start a new session |
| `/help` | Show available features |
| `/v1` | Switch to V1 graph |
| `/v2` | Switch to V2 graph |
| `/debug` | Toggle debug mode |

### Example Session

```
You: What's today's horoscope for Aries?
⏳ Processing...
🤖 Bot: Today brings positive energy for Aries...

You: Check PNR 1234567890
⏳ Processing...
🤖 Bot: PNR Status for 1234567890...
```

---

## 2. Chainlit Web Interface

A beautiful web-based chat interface for testing.

### Setup

```bash
# Install Chainlit
pip install chainlit

# Run the app
chainlit run chainlit_app.py -w --port 8000
```

### With Docker

```bash
# Start with dev profile
docker-compose --profile dev up chainlit

# Access at http://localhost:8000
```

### Features

- Real-time chat interface
- Message history
- Intent/domain metadata display
- Image rendering support
- Session management

---

## 3. Pytest Test Suite

Automated testing using pytest.

### Setup

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Or from requirements
pip install -r requirements-test.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_validators.py

# Run specific test class
pytest tests/test_validators.py::TestBirthDateValidation

# Run specific test
pytest tests/test_validators.py::TestBirthDateValidation::test_valid_dates

# Run with coverage
pytest --cov=bot --cov-report=html

# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run integration tests
pytest -m integration
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_domain_classifier.py # Domain classification tests
├── test_validators.py        # Input validation tests
├── test_rate_limiter.py      # Rate limiting tests
└── test_integration.py       # Integration tests
```

### Writing New Tests

```python
# tests/test_example.py
import pytest
from bot.some_module import some_function

class TestSomeFunction:
    """Test some_function behavior."""

    def test_basic_functionality(self):
        """Test basic case."""
        result = some_function("input")
        assert result == "expected"

    @pytest.mark.parametrize("input,expected", [
        ("case1", "result1"),
        ("case2", "result2"),
    ])
    def test_multiple_cases(self, input, expected):
        """Test multiple input/output cases."""
        assert some_function(input) == expected

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async function."""
        result = await async_function()
        assert result is not None
```

---

## 4. Logic Validation Script

End-to-end testing of bot intents and responses.

### Usage

```bash
# Test V1 graph
python test_bot_logic.py

# Test V2 graph
python test_bot_logic.py --v2

# Quick test (subset of cases)
python test_bot_logic.py --quick

# Test specific domain
python test_bot_logic.py --domain astrology

# Custom delay between tests
python test_bot_logic.py --delay 2.0
```

### Test Categories

| Domain | Test Cases |
|--------|------------|
| Astrology | Horoscope, Kundli, Dosha, Panchang, etc. |
| Travel | PNR Status, Train Status, Metro Routes |
| Utility | Weather, News, Reminders, Image Gen |
| Game | Word Game |
| Conversation | Greetings, Help |

### Output Example

```
============================================================
D23Bot Logic Validation
============================================================
Graph: V2 (domain-based)
Total Test Cases: 16
============================================================

══════════════════════════════════════════════════════════════
DOMAIN: ASTROLOGY
══════════════════════════════════════════════════════════════

──────────────────────────────────────────────────────────────
Category: Horoscope
Input: Aries horoscope
Status: ✅ PASS
Intent: get_horoscope | Domain: astrology
Response: Today brings positive energy for Aries...

──────────────────────────────────────────────────────────────
Category: Birth Chart
Input: Kundli for Rahul born on 15-08-1990 at 10:30 AM in Delhi
Status: ✅ PASS
Intent: birth_chart | Domain: astrology
Response: Here's the birth chart for Rahul...

============================================================
SUMMARY
============================================================
✅ Passed:   14
⚠️  Warnings: 2
❌ Failed:   0
Total:      16
============================================================

🎉 All tests passed!
```

---

## 5. API Testing with FastAPI

Test the HTTP API directly.

### Start the Server

```bash
# Local development
uvicorn main:app --host 0.0.0.0 --port 9002 --reload

# Or with Docker
docker-compose up -d bot
```

### Access API Docs

- Swagger UI: http://localhost:9002/docs
- ReDoc: http://localhost:9002/redoc

### Example Requests

```bash
# Health check
curl http://localhost:9002/

# Simulate WhatsApp webhook (requires proper format)
curl -X POST http://localhost:9002/webhook \
  -H "Content-Type: application/json" \
  -d '{"object": "whatsapp_business_account", ...}'
```

---

## 6. WhatsApp Testing

Test with actual WhatsApp integration.

### Local Development with ngrok

```bash
# 1. Start the bot
docker-compose up -d

# 2. Create ngrok tunnel
ngrok http 9002

# 3. Configure webhook in Facebook Developer Console
# Use the ngrok URL: https://xxxx.ngrok.io/webhook
```

### Test Phone Number

1. Go to Facebook Developer Console
2. Set up WhatsApp Test Number
3. Add your phone to allowed testers
4. Send messages to the test number

---

## 7. Testing Best Practices

### Before Committing

```bash
# 1. Run linter
ruff check .

# 2. Run formatter check
black --check .

# 3. Run tests
pytest

# 4. Run logic validation
python test_bot_logic.py --quick
```

### CI/CD Pipeline

The GitHub Actions CI workflow automatically runs:
- Linting (Ruff, Black)
- Type checking (MyPy)
- Unit tests (Pytest)
- Security scan (Bandit)
- Docker build

---

## 8. Test Coverage

### Generate Coverage Report

```bash
# Run with coverage
pytest --cov=bot --cov-report=html

# Open report
open htmlcov/index.html
```

### Coverage Goals

| Module | Target |
|--------|--------|
| Validators | 90%+ |
| Domain Classifier | 85%+ |
| Rate Limiter | 80%+ |
| Nodes | 70%+ |
| Integration | 60%+ |

---

## 9. Debugging Tips

### Enable Debug Logging

```bash
# Set environment variable
LOG_LEVEL=DEBUG python cli_chat.py

# Or in .env
LOG_LEVEL=DEBUG
```

### LangSmith Tracing

```bash
# Enable in .env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=d23bot

# View traces at https://smith.langchain.com/
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Database connection failed | Start PostgreSQL: `docker-compose up -d postgres` |
| OpenAI rate limit | Add delay between tests: `--delay 2.0` |
| Import errors | Check virtual env: `source venv/bin/activate` |
| Empty responses | Check API keys in `.env` |

---

## 10. Test Data

### Sample Birth Details

```python
{
    "date": "15-08-1990",
    "time": "10:30 AM",
    "place": "Delhi",
    "name": "Test User",
}
```

### Sample Queries by Domain

```python
# Astrology
"Aries horoscope"
"My kundli for 15-08-1990 10:30 AM Delhi"
"Check mangal dosha"

# Travel
"PNR 1234567890"
"Train 12301 status"

# Utility
"Weather in Mumbai"
"Latest news"
"Remind me in 5 minutes"

# Game
"Play word game"
```

---

## Support

- **Issues:** https://github.com/your-org/d23bot/issues
- **Documentation:** See readme.md
