"""
Pytest Configuration and Fixtures

This module provides shared fixtures for testing D23Bot.
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv

# Load test environment
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_whatsapp_message() -> dict:
    """Create a mock WhatsApp message for testing."""
    def _create_message(text: str, from_number: str = "test_user_123") -> dict:
        return {
            "message_id": str(uuid.uuid4()),
            "from_number": from_number,
            "phone_number_id": "test_server",
            "timestamp": datetime.now().isoformat(),
            "message_type": "text",
            "text": text,
            "media_id": None,
        }
    return _create_message


@pytest.fixture
def sample_messages() -> list:
    """Sample test messages for various intents."""
    return [
        # Astrology
        {"text": "Aries horoscope", "expected_domain": "astrology"},
        {"text": "My kundli for 15-08-1990 10:30 AM Delhi", "expected_domain": "astrology"},
        {"text": "Check mangal dosha", "expected_domain": "astrology"},
        {"text": "Today's panchang", "expected_domain": "astrology"},

        # Travel
        {"text": "PNR 1234567890", "expected_domain": "travel"},
        {"text": "Train 12301 running status", "expected_domain": "travel"},
        {"text": "Metro from Dwarka to Rajiv Chowk", "expected_domain": "travel"},

        # Utility
        {"text": "Weather in Mumbai", "expected_domain": "utility"},
        {"text": "Latest news", "expected_domain": "utility"},
        {"text": "Remind me in 5 minutes", "expected_domain": "utility"},
        {"text": "Generate image of a cat", "expected_domain": "utility"},

        # Game
        {"text": "Play word game", "expected_domain": "game"},

        # Conversation
        {"text": "Hello, how are you?", "expected_domain": "conversation"},
        {"text": "What can you do?", "expected_domain": "conversation"},
    ]


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("openai.AsyncOpenAI") as mock:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(content="Mocked response")
                    )
                ]
            )
        )
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    with patch("asyncpg.create_pool") as mock:
        mock_pool = MagicMock()
        mock_pool.acquire = AsyncMock()
        mock_pool.release = AsyncMock()
        mock.return_value = mock_pool
        yield mock_pool


@pytest.fixture
def test_birth_details() -> dict:
    """Sample birth details for astrology testing."""
    return {
        "date": "15-08-1990",
        "time": "10:30 AM",
        "place": "Delhi",
        "name": "Test User",
    }


@pytest.fixture
def mock_astrology_api():
    """Mock astrology API responses."""
    return {
        "horoscope": {
            "sun_sign": "Leo",
            "prediction": "Today is a great day for new beginnings.",
            "lucky_number": 7,
            "lucky_color": "Gold",
        },
        "kundli": {
            "ascendant": "Libra",
            "moon_sign": "Cancer",
            "planets": [
                {"name": "Sun", "sign": "Leo", "house": 11},
                {"name": "Moon", "sign": "Cancer", "house": 10},
            ],
        },
        "dosha": {
            "mangal_dosha": False,
            "kaal_sarp_dosha": False,
            "remedies": [],
        },
    }


# Async fixture helper
@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
