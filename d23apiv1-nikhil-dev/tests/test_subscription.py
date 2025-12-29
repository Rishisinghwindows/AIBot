"""
Tests for Subscription System

Tests for:
- SubscriptionService (subscribe, unsubscribe, manage)
- HoroscopeScheduler (scheduling, sending)
- TransitService (transit detection, alerts)
- SubscriptionNode (conversation handling)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import uuid


# =============================================================================
# SUBSCRIPTION SERVICE TESTS
# =============================================================================

class TestSubscriptionService:
    """Tests for SubscriptionService."""

    @pytest.fixture
    def mock_store(self):
        """Mock the data store."""
        with patch("bot.services.subscription_service.get_store") as mock:
            store = MagicMock()
            store.get_subscription = AsyncMock(return_value=None)
            store.save_subscription = AsyncMock(return_value=True)
            store.delete_subscription = AsyncMock(return_value=True)
            store.get_subscriptions_by_type = AsyncMock(return_value=[])
            store.get_user_subscriptions = AsyncMock(return_value=[])
            mock.return_value = store
            yield store

    @pytest.mark.asyncio
    async def test_subscribe_daily_horoscope(self, mock_store):
        """Test subscribing to daily horoscope."""
        from bot.services.subscription_service import (
            SubscriptionService,
            SubscriptionType,
        )

        service = SubscriptionService()
        result = await service.subscribe(
            phone="919999999999",
            subscription_type=SubscriptionType.DAILY_HOROSCOPE,
            zodiac_sign="aries",
            preferred_time="07:00"
        )

        assert result["success"] is True
        mock_store.save_subscription.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_already_subscribed(self, mock_store):
        """Test subscribing when already subscribed."""
        from bot.services.subscription_service import (
            SubscriptionService,
            SubscriptionType,
            Subscription,
        )

        # Mock existing subscription
        existing = Subscription(
            phone="919999999999",
            subscription_type=SubscriptionType.DAILY_HOROSCOPE,
            zodiac_sign="aries",
            enabled=True,
        )
        mock_store.get_subscription.return_value = existing

        service = SubscriptionService()
        result = await service.subscribe(
            phone="919999999999",
            subscription_type=SubscriptionType.DAILY_HOROSCOPE,
            zodiac_sign="aries",
        )

        assert result["success"] is False
        assert "already subscribed" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_unsubscribe(self, mock_store):
        """Test unsubscribing."""
        from bot.services.subscription_service import (
            SubscriptionService,
            SubscriptionType,
            Subscription,
        )

        # Mock existing subscription
        existing = Subscription(
            phone="919999999999",
            subscription_type=SubscriptionType.DAILY_HOROSCOPE,
            zodiac_sign="aries",
            enabled=True,
        )
        mock_store.get_subscription.return_value = existing

        service = SubscriptionService()
        result = await service.unsubscribe(
            phone="919999999999",
            subscription_type=SubscriptionType.DAILY_HOROSCOPE,
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_unsubscribe_not_subscribed(self, mock_store):
        """Test unsubscribing when not subscribed."""
        from bot.services.subscription_service import (
            SubscriptionService,
            SubscriptionType,
        )

        mock_store.get_subscription.return_value = None

        service = SubscriptionService()
        result = await service.unsubscribe(
            phone="919999999999",
            subscription_type=SubscriptionType.DAILY_HOROSCOPE,
        )

        assert result["success"] is False
        assert "not subscribed" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_is_subscribed(self, mock_store):
        """Test checking subscription status."""
        from bot.services.subscription_service import (
            SubscriptionService,
            SubscriptionType,
            Subscription,
        )

        existing = Subscription(
            phone="919999999999",
            subscription_type=SubscriptionType.DAILY_HOROSCOPE,
            zodiac_sign="aries",
            enabled=True,
        )
        mock_store.get_subscription.return_value = existing

        service = SubscriptionService()
        is_subscribed = await service.is_subscribed(
            phone="919999999999",
            subscription_type=SubscriptionType.DAILY_HOROSCOPE,
        )

        assert is_subscribed is True

    @pytest.mark.asyncio
    async def test_get_user_subscriptions(self, mock_store):
        """Test getting all user subscriptions."""
        from bot.services.subscription_service import (
            SubscriptionService,
            SubscriptionType,
            Subscription,
        )

        subs = [
            Subscription(
                phone="919999999999",
                subscription_type=SubscriptionType.DAILY_HOROSCOPE,
                zodiac_sign="aries",
                enabled=True,
            ),
            Subscription(
                phone="919999999999",
                subscription_type=SubscriptionType.TRANSIT_ALERTS,
                enabled=True,
            ),
        ]
        mock_store.get_user_subscriptions.return_value = subs

        service = SubscriptionService()
        result = await service.get_user_subscriptions("919999999999")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_due_subscribers(self, mock_store):
        """Test getting subscribers due for notification."""
        from bot.services.subscription_service import (
            SubscriptionService,
            SubscriptionType,
            Subscription,
        )

        subs = [
            Subscription(
                phone="919999999999",
                subscription_type=SubscriptionType.DAILY_HOROSCOPE,
                zodiac_sign="aries",
                preferred_time="07:00",
                enabled=True,
            ),
        ]
        mock_store.get_subscriptions_by_type.return_value = subs

        service = SubscriptionService()
        result = await service.get_due_subscribers(
            SubscriptionType.DAILY_HOROSCOPE,
            "07:00"
        )

        assert len(result) == 1
        assert result[0].zodiac_sign == "aries"


# =============================================================================
# HOROSCOPE SCHEDULER TESTS
# =============================================================================

class TestHoroscopeScheduler:
    """Tests for HoroscopeScheduler."""

    @pytest.fixture
    def mock_services(self):
        """Mock all required services."""
        with patch("bot.services.horoscope_scheduler.get_subscription_service") as mock_sub, \
             patch("bot.services.horoscope_scheduler.send_whatsapp_message") as mock_wa:

            sub_service = MagicMock()
            sub_service.get_due_subscribers = AsyncMock(return_value=[])
            mock_sub.return_value = sub_service

            mock_wa.return_value = AsyncMock(return_value=True)

            yield {
                "subscription_service": sub_service,
                "whatsapp": mock_wa,
            }

    @pytest.mark.asyncio
    async def test_scheduler_initialization(self, mock_services):
        """Test scheduler can be initialized."""
        from bot.services.horoscope_scheduler import HoroscopeScheduler

        scheduler = HoroscopeScheduler()
        assert scheduler is not None
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_generate_horoscope_message(self, mock_services):
        """Test horoscope message generation."""
        from bot.services.horoscope_scheduler import HoroscopeScheduler

        scheduler = HoroscopeScheduler()

        with patch.object(scheduler, "_generate_horoscope") as mock_gen:
            mock_gen.return_value = {
                "prediction": "Great day ahead!",
                "lucky_number": 7,
                "lucky_color": "Blue",
            }

            message = await scheduler._format_horoscope_message("aries")

            assert "aries" in message.lower() or "Aries" in message


# =============================================================================
# TRANSIT SERVICE TESTS
# =============================================================================

class TestTransitService:
    """Tests for TransitService."""

    @pytest.fixture
    def mock_ephemeris(self):
        """Mock ephemeris calculations."""
        with patch("bot.services.transit_service.get_planet_position") as mock:
            mock.return_value = {"sign": "aries", "degree": 15.5}
            yield mock

    @pytest.mark.asyncio
    async def test_get_upcoming_transits(self, mock_ephemeris):
        """Test getting upcoming transits."""
        from bot.services.transit_service import TransitService

        service = TransitService()
        transits = await service.get_upcoming_transits(days=30)

        assert isinstance(transits, list)

    @pytest.mark.asyncio
    async def test_is_planet_retrograde(self, mock_ephemeris):
        """Test retrograde detection."""
        from bot.services.transit_service import TransitService

        service = TransitService()

        # Test known retrograde periods (mocked)
        with patch.object(service, "_get_retrograde_status") as mock_retro:
            mock_retro.return_value = True
            is_retro = service.is_planet_retrograde("mercury")
            assert isinstance(is_retro, bool)

    @pytest.mark.asyncio
    async def test_get_personalized_transits(self, mock_ephemeris):
        """Test personalized transit impacts."""
        from bot.services.transit_service import TransitService

        with patch("bot.services.transit_service.get_store") as mock_store:
            store = MagicMock()
            store.get_user = AsyncMock(return_value=MagicMock(
                moon_sign="cancer",
                sun_sign="leo"
            ))
            mock_store.return_value = store

            service = TransitService()
            result = await service.get_personalized_transits("919999999999")

            assert "upcoming_transits" in result
            assert "current_retrogrades" in result


# =============================================================================
# SUBSCRIPTION NODE TESTS
# =============================================================================

class TestSubscriptionNode:
    """Tests for subscription node handler."""

    @pytest.fixture
    def mock_state(self):
        """Create mock bot state."""
        def _create(query: str, phone: str = "919999999999") -> dict:
            return {
                "current_query": query,
                "whatsapp_message": {"from_number": phone},
                "extracted_entities": {},
                "intent": "subscription",
            }
        return _create

    @pytest.fixture
    def mock_services(self):
        """Mock subscription services."""
        with patch("bot.nodes.subscription_node.get_subscription_service") as mock_sub, \
             patch("bot.nodes.subscription_node.get_transit_service") as mock_transit, \
             patch("bot.nodes.subscription_node.get_store") as mock_store:

            sub_service = MagicMock()
            sub_service.subscribe = AsyncMock(return_value={"success": True})
            sub_service.unsubscribe = AsyncMock(return_value={"success": True})
            sub_service.is_subscribed = AsyncMock(return_value=False)
            sub_service.get_user_subscriptions = AsyncMock(return_value=[])
            mock_sub.return_value = sub_service

            transit_service = MagicMock()
            transit_service.get_personalized_transits = AsyncMock(return_value={
                "upcoming_transits": [],
                "current_retrogrades": [],
            })
            mock_transit.return_value = transit_service

            store = MagicMock()
            store.get_user = AsyncMock(return_value=None)
            mock_store.return_value = store

            yield {
                "subscription": sub_service,
                "transit": transit_service,
                "store": store,
            }

    @pytest.mark.asyncio
    async def test_subscribe_horoscope_with_sign(self, mock_state, mock_services):
        """Test subscribing to horoscope with zodiac sign."""
        from bot.nodes.subscription_node import handle_subscription

        state = mock_state("subscribe horoscope aries")
        result = await handle_subscription(state)

        assert result["response_type"] == "text"
        assert "subscribed" in result["response_text"].lower()
        mock_services["subscription"].subscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_horoscope_without_sign(self, mock_state, mock_services):
        """Test subscribing without zodiac sign asks for it."""
        from bot.nodes.subscription_node import handle_subscription

        state = mock_state("subscribe horoscope")
        result = await handle_subscription(state)

        assert result["response_type"] == "text"
        # Should ask for zodiac sign
        assert "sign" in result["response_text"].lower() or "zodiac" in result["response_text"].lower()

    @pytest.mark.asyncio
    async def test_subscribe_transit_alerts(self, mock_state, mock_services):
        """Test subscribing to transit alerts."""
        from bot.nodes.subscription_node import handle_subscription

        state = mock_state("subscribe transit alerts")
        result = await handle_subscription(state)

        assert result["response_type"] == "text"
        assert "subscribed" in result["response_text"].lower() or "transit" in result["response_text"].lower()

    @pytest.mark.asyncio
    async def test_unsubscribe_horoscope(self, mock_state, mock_services):
        """Test unsubscribing from horoscope."""
        from bot.nodes.subscription_node import handle_subscription

        state = mock_state("unsubscribe horoscope")
        result = await handle_subscription(state)

        assert result["response_type"] == "text"
        mock_services["subscription"].unsubscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_view_subscriptions_empty(self, mock_state, mock_services):
        """Test viewing subscriptions when none exist."""
        from bot.nodes.subscription_node import handle_subscription

        state = mock_state("my subscriptions")
        result = await handle_subscription(state)

        assert result["response_type"] == "text"
        assert "subscription" in result["response_text"].lower()

    @pytest.mark.asyncio
    async def test_view_subscriptions_with_active(self, mock_state, mock_services):
        """Test viewing active subscriptions."""
        from bot.nodes.subscription_node import handle_subscription
        from bot.services.subscription_service import Subscription, SubscriptionType

        # Mock active subscription
        mock_services["subscription"].get_user_subscriptions.return_value = [
            Subscription(
                phone="919999999999",
                subscription_type=SubscriptionType.DAILY_HOROSCOPE,
                zodiac_sign="aries",
                preferred_time="07:00",
                enabled=True,
            )
        ]

        state = mock_state("my subscriptions")
        result = await handle_subscription(state)

        assert result["response_type"] == "text"
        assert "horoscope" in result["response_text"].lower()

    @pytest.mark.asyncio
    async def test_view_upcoming_transits(self, mock_state, mock_services):
        """Test viewing upcoming transits."""
        from bot.nodes.subscription_node import handle_subscription

        mock_services["transit"].get_personalized_transits.return_value = {
            "upcoming_transits": [
                {
                    "planet": "jupiter",
                    "date": "2024-02-15",
                    "description": "Jupiter enters Taurus",
                }
            ],
            "current_retrogrades": [],
        }

        state = mock_state("upcoming transits")
        result = await handle_subscription(state)

        assert result["response_type"] == "text"
        assert "transit" in result["response_text"].lower()

    @pytest.mark.asyncio
    async def test_already_subscribed(self, mock_state, mock_services):
        """Test subscribing when already subscribed."""
        from bot.nodes.subscription_node import handle_subscription

        mock_services["subscription"].is_subscribed.return_value = True

        state = mock_state("subscribe horoscope aries")
        result = await handle_subscription(state)

        assert result["response_type"] == "text"
        assert "already" in result["response_text"].lower()

    @pytest.mark.asyncio
    async def test_subscription_help(self, mock_state, mock_services):
        """Test subscription help message."""
        from bot.nodes.subscription_node import handle_subscription

        state = mock_state("subscription")  # Generic query
        result = await handle_subscription(state)

        assert result["response_type"] == "text"
        # Should show help with available options
        assert "subscribe" in result["response_text"].lower()

    @pytest.mark.asyncio
    async def test_no_phone_number(self, mock_services):
        """Test handling when phone number is missing."""
        from bot.nodes.subscription_node import handle_subscription

        state = {
            "current_query": "subscribe horoscope",
            "whatsapp_message": {},  # No phone
            "extracted_entities": {},
        }

        result = await handle_subscription(state)

        assert result["response_type"] == "text"
        # Should show error about user identification


# =============================================================================
# INTENT DETECTION TESTS FOR SUBSCRIPTION
# =============================================================================

class TestSubscriptionIntentDetection:
    """Tests for subscription intent detection."""

    @pytest.mark.parametrize("query,expected_action", [
        ("subscribe horoscope", "subscribe_horoscope"),
        ("subscribe daily horoscope aries", "subscribe_horoscope"),
        ("subscribe transit alerts", "subscribe_transit"),
        ("subscribe planetary alerts", "subscribe_transit"),
        ("unsubscribe horoscope", "unsubscribe_horoscope"),
        ("stop horoscope", "unsubscribe_horoscope"),
        ("cancel daily horoscope", "unsubscribe_horoscope"),
        ("unsubscribe alerts", "unsubscribe_transit"),
        ("stop transit alerts", "unsubscribe_transit"),
        ("my subscriptions", "view_subscriptions"),
        ("what am i subscribed to", "view_subscriptions"),
        ("upcoming transits", "view_transits"),
        ("planetary transits", "view_transits"),
    ])
    def test_action_detection(self, query, expected_action):
        """Test action detection from query."""
        from bot.nodes.subscription_node import _determine_action

        action = _determine_action(query)
        assert action == expected_action, f"Query '{query}' should map to '{expected_action}', got '{action}'"


# =============================================================================
# ZODIAC EXTRACTION TESTS
# =============================================================================

class TestZodiacExtraction:
    """Tests for zodiac sign extraction."""

    @pytest.mark.parametrize("query,expected_sign", [
        ("subscribe horoscope aries", "aries"),
        ("subscribe horoscope Taurus", "taurus"),
        ("daily horoscope for leo", "leo"),
        ("subscribe mesh", "aries"),  # Hindi
        ("horoscope vrishabh", "taurus"),  # Hindi
        ("subscribe kanya sign", "virgo"),  # Hindi
        ("subscribe horoscope CAPRICORN", "capricorn"),
        ("subscribe horoscope sagittarius please", "sagittarius"),
    ])
    def test_zodiac_extraction(self, query, expected_sign):
        """Test zodiac sign extraction from query."""
        from bot.nodes.subscription_node import _extract_zodiac_from_query

        sign = _extract_zodiac_from_query(query)
        assert sign == expected_sign, f"Query '{query}' should extract '{expected_sign}', got '{sign}'"

    @pytest.mark.parametrize("query", [
        "subscribe horoscope",
        "daily horoscope please",
        "subscribe",
    ])
    def test_no_zodiac_found(self, query):
        """Test when no zodiac sign is in query."""
        from bot.nodes.subscription_node import _extract_zodiac_from_query

        sign = _extract_zodiac_from_query(query)
        assert sign is None


# =============================================================================
# TIME EXTRACTION TESTS
# =============================================================================

class TestTimeExtraction:
    """Tests for preferred time extraction."""

    @pytest.mark.parametrize("query,expected_time", [
        ("subscribe horoscope at 7am", "07:00"),
        ("subscribe horoscope 8:30 am", "08:30"),
        ("subscribe horoscope morning", "07:00"),
        ("subscribe horoscope evening", "18:00"),
        ("subscribe horoscope night", "21:00"),
        ("subscribe horoscope 6pm", "18:00"),
        ("daily horoscope at 10:00", "10:00"),
    ])
    def test_time_extraction(self, query, expected_time):
        """Test time extraction from query."""
        from bot.nodes.subscription_node import _extract_time_from_query

        time = _extract_time_from_query(query)
        assert time == expected_time, f"Query '{query}' should extract '{expected_time}', got '{time}'"

    @pytest.mark.parametrize("query", [
        "subscribe horoscope aries",
        "daily horoscope",
    ])
    def test_no_time_found(self, query):
        """Test when no time preference in query."""
        from bot.nodes.subscription_node import _extract_time_from_query

        time = _extract_time_from_query(query)
        assert time is None


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestSubscriptionIntegration:
    """Integration tests for full subscription flow."""

    @pytest.fixture
    def mock_message(self):
        """Create mock WhatsApp message."""
        def _create(text: str) -> dict:
            return {
                "message_id": str(uuid.uuid4()),
                "from_number": "919999999999",
                "phone_number_id": "test_server",
                "timestamp": datetime.now().isoformat(),
                "message_type": "text",
                "text": text,
                "media_id": None,
            }
        return _create

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_subscription_flow(self, mock_message):
        """Test complete subscription flow: subscribe -> view -> unsubscribe."""
        # This test requires mocking the graph execution
        # Skip if no proper test environment
        pytest.skip("Requires full graph setup")

    @pytest.mark.asyncio
    async def test_subscription_state_persistence(self):
        """Test that subscriptions persist correctly."""
        # This would test with actual database
        pytest.skip("Requires database connection")
