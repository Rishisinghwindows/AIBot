"""
Integration Tests for D23Bot

Tests the full message processing flow through the graph.
Requires database connection for full testing.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock


class TestGraphIntegration:
    """Integration tests for the bot graph."""

    @pytest.fixture
    def mock_message(self):
        """Create a mock WhatsApp message."""
        def _create(text: str) -> dict:
            return {
                "message_id": str(uuid.uuid4()),
                "from_number": f"test_{uuid.uuid4().hex[:8]}",
                "phone_number_id": "test_server",
                "timestamp": datetime.now().isoformat(),
                "message_type": "text",
                "text": text,
                "media_id": None,
            }
        return _create

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # Skip by default, enable with proper DB setup
        reason="Requires database connection"
    )
    async def test_horoscope_flow(self, mock_message):
        """Test horoscope query flow."""
        from bot.graph_v2 import process_message_v2

        message = mock_message("What's today's horoscope for Aries?")
        result = await process_message_v2(message)

        assert "response_text" in result
        assert result["domain"] == "astrology"
        assert result.get("error") is None

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,
        reason="Requires database connection"
    )
    async def test_weather_flow(self, mock_message):
        """Test weather query flow."""
        from bot.graph_v2 import process_message_v2

        message = mock_message("Weather in Mumbai")
        result = await process_message_v2(message)

        assert "response_text" in result
        assert result["domain"] == "utility"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,
        reason="Requires database connection"
    )
    async def test_pnr_flow(self, mock_message):
        """Test PNR status flow."""
        from bot.graph_v2 import process_message_v2

        message = mock_message("Check PNR 1234567890")
        result = await process_message_v2(message)

        assert "response_text" in result
        assert result["domain"] == "travel"

    @pytest.mark.asyncio
    async def test_state_creation(self):
        """Test initial state creation."""
        from bot.state import WhatsAppMessage, create_initial_state

        wa_message = WhatsAppMessage(
            message_id="test_123",
            from_number="user_456",
            phone_number_id="server_789",
            timestamp="2024-01-01T00:00:00",
            message_type="text",
            text="Hello world",
            media_id=None,
        )

        state = create_initial_state(wa_message)

        assert state["current_query"] == "Hello world"
        assert state["user_phone"] == "user_456"
        assert state["response_text"] is None
        assert state["error"] is None


class TestMockedIntegration:
    """Integration tests with mocked external services."""

    @pytest.fixture
    def mock_all_externals(self):
        """Mock all external API calls."""
        with patch("bot.nodes.weather.get_weather") as mock_weather, \
             patch("bot.nodes.news_node.get_news") as mock_news, \
             patch("openai.AsyncOpenAI") as mock_openai:

            mock_weather.return_value = {
                "location": "Mumbai",
                "temperature": 28,
                "condition": "Sunny",
            }

            mock_news.return_value = [
                {"title": "Test News 1", "source": "Test"},
                {"title": "Test News 2", "source": "Test"},
            ]

            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content="Test response"))]
                )
            )
            mock_openai.return_value = mock_client

            yield {
                "weather": mock_weather,
                "news": mock_news,
                "openai": mock_client,
            }

    @pytest.mark.asyncio
    async def test_domain_classification_only(self):
        """Test domain classification without full graph execution."""
        from bot.graphs.domain_classifier import classify_domain

        test_cases = [
            ("horoscope aries", "astrology"),
            ("pnr status", "travel"),
            ("weather delhi", "utility"),
            ("play game", "game"),
            ("hello there", "conversation"),
        ]

        for query, expected_domain in test_cases:
            state = {"current_query": query}
            result = classify_domain(state)
            assert result["domain"] == expected_domain, \
                f"Failed for query: {query}"


class TestErrorHandling:
    """Test error handling in the graph."""

    @pytest.mark.asyncio
    async def test_empty_message_handling(self):
        """Test handling of empty messages."""
        from bot.state import WhatsAppMessage, create_initial_state

        wa_message = WhatsAppMessage(
            message_id="test_123",
            from_number="user_456",
            phone_number_id="server_789",
            timestamp="2024-01-01T00:00:00",
            message_type="text",
            text="",
            media_id=None,
        )

        state = create_initial_state(wa_message)
        assert state["current_query"] == ""

    @pytest.mark.asyncio
    async def test_special_characters_in_message(self):
        """Test handling of special characters."""
        from bot.state import WhatsAppMessage, create_initial_state

        special_texts = [
            "Hello! How are you?",
            "What's the weather?",
            "Test @#$%^&*()",
            "Unicode: नमस्ते 你好",
            "Emoji: 🔮✨",
        ]

        for text in special_texts:
            wa_message = WhatsAppMessage(
                message_id="test_123",
                from_number="user_456",
                phone_number_id="server_789",
                timestamp="2024-01-01T00:00:00",
                message_type="text",
                text=text,
                media_id=None,
            )

            state = create_initial_state(wa_message)
            assert state["current_query"] == text
