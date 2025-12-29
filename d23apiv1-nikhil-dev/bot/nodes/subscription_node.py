"""
Subscription Management Node

Handles user subscription requests for:
- Daily horoscope
- Transit alerts
- Weekly/monthly predictions

Commands:
- "subscribe daily horoscope" / "subscribe horoscope"
- "subscribe transit alerts"
- "unsubscribe horoscope"
- "my subscriptions"
"""

import logging
import re
from typing import Dict, Any, Optional

from bot.state import BotState
from bot.services.subscription_service import (
    get_subscription_service,
    SubscriptionType,
)
from bot.services.transit_service import get_transit_service
from bot.stores import get_store

logger = logging.getLogger(__name__)

INTENT = "subscription"


async def handle_subscription(state: BotState) -> dict:
    """
    Handle subscription-related requests.

    Supported actions:
    - Subscribe to daily horoscope
    - Subscribe to transit alerts
    - Unsubscribe
    - View subscriptions
    - View upcoming transits

    Args:
        state: Current bot state

    Returns:
        Response dict
    """
    query = state.get("current_query", "").lower()
    phone = state.get("whatsapp_message", {}).get("from_number", "")
    entities = state.get("extracted_entities", {})

    if not phone:
        return _error_response("Could not identify user.")

    # Determine action from query
    action = _determine_action(query)

    if action == "subscribe_horoscope":
        return await _subscribe_horoscope(phone, entities, query)
    elif action == "subscribe_transit":
        return await _subscribe_transit(phone, entities)
    elif action == "unsubscribe_horoscope":
        return await _unsubscribe(phone, SubscriptionType.DAILY_HOROSCOPE)
    elif action == "unsubscribe_transit":
        return await _unsubscribe(phone, SubscriptionType.TRANSIT_ALERTS)
    elif action == "view_subscriptions":
        return await _view_subscriptions(phone)
    elif action == "view_transits":
        return await _view_transits(phone)
    else:
        return _subscription_help()


def _determine_action(query: str) -> str:
    """Determine the subscription action from query."""
    query = query.lower()

    # View patterns (check first to avoid conflicts with "subscribed")
    if any(phrase in query for phrase in ["my subscription", "subscriptions", "what am i subscribed", "show subscription"]):
        return "view_subscriptions"

    # Unsubscribe patterns
    if any(word in query for word in ["unsubscribe", "stop", "cancel"]):
        if any(word in query for word in ["horoscope", "rashifal", "daily"]):
            return "unsubscribe_horoscope"
        if any(word in query for word in ["transit", "alert", "planetary"]):
            return "unsubscribe_transit"
        # Default unsubscribe from horoscope
        return "unsubscribe_horoscope"

    # Subscribe patterns
    if any(word in query for word in ["subscribe", "start", "enable", "daily"]):
        if any(word in query for word in ["transit", "alert", "planetary"]):
            return "subscribe_transit"
        if any(word in query for word in ["horoscope", "rashifal", "rashi"]):
            return "subscribe_horoscope"
        # Default to horoscope
        return "subscribe_horoscope"

    # View transits pattern
    if any(phrase in query for phrase in ["transit", "planetary", "upcoming planet"]):
        return "view_transits"

    return "unknown"


async def _subscribe_horoscope(
    phone: str,
    entities: dict,
    query: str
) -> dict:
    """Subscribe user to daily horoscope."""
    service = get_subscription_service()
    store = get_store()

    # Check if already subscribed
    if await service.is_subscribed(phone, SubscriptionType.DAILY_HOROSCOPE):
        return {
            "response_text": (
                "*Daily Horoscope*\n\n"
                "You're already subscribed to daily horoscope!\n\n"
                "_Reply 'unsubscribe horoscope' to stop._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    # Get zodiac sign
    zodiac_sign = entities.get("zodiac_sign")

    # Try to extract from query
    if not zodiac_sign:
        zodiac_sign = _extract_zodiac_from_query(query)

    # Try to get from user profile
    if not zodiac_sign:
        user = await store.get_user(phone)
        if user and user.sun_sign:
            zodiac_sign = user.sun_sign

    # If still no zodiac, ask user
    if not zodiac_sign:
        return {
            "response_text": (
                "*Subscribe to Daily Horoscope*\n\n"
                "I need your zodiac sign to send personalized horoscope.\n\n"
                "Please reply with your sign:\n"
                "_Example: Subscribe horoscope Aries_\n\n"
                "Or provide your birth details and I'll calculate it!"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    # Extract preferred time if mentioned
    preferred_time = _extract_time_from_query(query) or "07:00"

    # Subscribe
    result = await service.subscribe(
        phone=phone,
        subscription_type=SubscriptionType.DAILY_HOROSCOPE,
        zodiac_sign=zodiac_sign.lower(),
        preferred_time=preferred_time
    )

    if result["success"]:
        return {
            "response_text": (
                "✅ *Subscribed to Daily Horoscope!*\n\n"
                f"🌟 Sign: *{zodiac_sign.title()}*\n"
                f"⏰ Time: *{preferred_time} IST*\n\n"
                "You'll receive your personalized horoscope every day.\n\n"
                "_Reply 'unsubscribe horoscope' anytime to stop._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }
    else:
        return _error_response(result.get("message", "Failed to subscribe"))


async def _subscribe_transit(phone: str, entities: dict) -> dict:
    """Subscribe user to transit alerts."""
    service = get_subscription_service()
    store = get_store()

    # Check if already subscribed
    if await service.is_subscribed(phone, SubscriptionType.TRANSIT_ALERTS):
        return {
            "response_text": (
                "*Transit Alerts*\n\n"
                "You're already subscribed to planetary transit alerts!\n\n"
                "_Reply 'unsubscribe alerts' to stop._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    # Get user's moon sign for personalized alerts
    user = await store.get_user(phone)
    moon_sign = user.moon_sign if user else None

    # Subscribe
    result = await service.subscribe(
        phone=phone,
        subscription_type=SubscriptionType.TRANSIT_ALERTS,
        moon_sign=moon_sign,
        preferred_time="08:00"
    )

    if result["success"]:
        response = (
            "✅ *Subscribed to Transit Alerts!*\n\n"
            "🪐 You'll receive alerts for:\n"
            "- Major planetary sign changes\n"
            "- Retrograde periods\n"
            "- Important conjunctions\n\n"
        )

        if moon_sign:
            response += f"_Personalized for your Moon sign: {moon_sign.title()}_\n\n"
        else:
            response += (
                "_Tip: Save your birth details for personalized transit impacts!_\n\n"
            )

        response += "_Reply 'unsubscribe alerts' anytime to stop._"

        return {
            "response_text": response,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }
    else:
        return _error_response(result.get("message", "Failed to subscribe"))


async def _unsubscribe(phone: str, subscription_type: SubscriptionType) -> dict:
    """Unsubscribe user from a subscription type."""
    service = get_subscription_service()

    result = await service.unsubscribe(phone, subscription_type)

    type_name = "Daily Horoscope" if subscription_type == SubscriptionType.DAILY_HOROSCOPE else "Transit Alerts"

    if result["success"]:
        return {
            "response_text": (
                f"✅ *Unsubscribed from {type_name}*\n\n"
                "You won't receive these notifications anymore.\n\n"
                "_You can subscribe again anytime!_"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }
    else:
        return _error_response(f"Failed to unsubscribe from {type_name}")


async def _view_subscriptions(phone: str) -> dict:
    """View user's active subscriptions."""
    service = get_subscription_service()
    subscriptions = await service.get_user_subscriptions(phone)

    if not subscriptions:
        return {
            "response_text": (
                "*Your Subscriptions*\n\n"
                "You don't have any active subscriptions.\n\n"
                "*Available subscriptions:*\n"
                "- Daily Horoscope - 'subscribe horoscope'\n"
                "- Transit Alerts - 'subscribe transit alerts'"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    lines = ["*Your Active Subscriptions*\n"]

    for sub in subscriptions:
        if sub.enabled:
            if sub.subscription_type == SubscriptionType.DAILY_HOROSCOPE:
                lines.append(f"🌟 *Daily Horoscope*")
                lines.append(f"   Sign: {sub.zodiac_sign.title() if sub.zodiac_sign else 'Not set'}")
                lines.append(f"   Time: {sub.preferred_time} IST")
            elif sub.subscription_type == SubscriptionType.TRANSIT_ALERTS:
                lines.append(f"🪐 *Transit Alerts*")
                lines.append(f"   Planets: {', '.join(sub.alert_planets[:3])}...")
            lines.append("")

    lines.append("_Reply 'unsubscribe [type]' to stop any subscription._")

    return {
        "response_text": "\n".join(lines),
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }


async def _view_transits(phone: str) -> dict:
    """View upcoming planetary transits."""
    service = get_transit_service()
    store = get_store()

    # Get personalized transits
    transit_data = await service.get_personalized_transits(phone)

    lines = ["🪐 *Upcoming Planetary Transits*\n"]

    # Current retrogrades
    if transit_data["current_retrogrades"]:
        lines.append("*Currently Retrograde:*")
        for retro in transit_data["current_retrogrades"]:
            lines.append(f"- {retro['planet'].title()} (until {retro['until']})")
        lines.append("")

    # Upcoming transits
    if transit_data["upcoming_transits"]:
        lines.append("*Coming Up:*")
        for transit in transit_data["upcoming_transits"][:5]:
            emoji = _get_planet_emoji(transit["planet"])
            lines.append(f"\n{emoji} *{transit['planet'].title()}* - {transit['date']}")
            lines.append(f"   {transit['description']}")
            if transit.get("personal_impact"):
                lines.append(f"   _Your impact: {transit['personal_impact']}_")
    else:
        lines.append("No major transits in the next 30 days.")

    lines.append("")
    lines.append("_Subscribe to transit alerts for notifications!_")

    return {
        "response_text": "\n".join(lines),
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }


def _subscription_help() -> dict:
    """Return subscription help message."""
    return {
        "response_text": (
            "*Subscription Services*\n\n"
            "I can send you personalized notifications!\n\n"
            "*Available:*\n"
            "🌟 *Daily Horoscope*\n"
            "   'subscribe horoscope [sign]'\n\n"
            "🪐 *Transit Alerts*\n"
            "   'subscribe transit alerts'\n\n"
            "*Manage:*\n"
            "- 'my subscriptions' - view active\n"
            "- 'unsubscribe [type]' - stop\n"
            "- 'upcoming transits' - view transits"
        ),
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }


def _error_response(message: str) -> dict:
    """Return error response."""
    return {
        "response_text": f"*Subscription*\n\n{message}",
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }


def _extract_zodiac_from_query(query: str) -> Optional[str]:
    """Extract zodiac sign from query."""
    signs = [
        "aries", "taurus", "gemini", "cancer",
        "leo", "virgo", "libra", "scorpio",
        "sagittarius", "capricorn", "aquarius", "pisces",
        # Hindi names
        "mesh", "vrishabh", "mithun", "kark",
        "singh", "kanya", "tula", "vrishchik",
        "dhanu", "makar", "kumbh", "meen"
    ]

    query_lower = query.lower()
    for sign in signs:
        if sign in query_lower:
            # Map Hindi to English
            hindi_to_english = {
                "mesh": "aries", "vrishabh": "taurus", "mithun": "gemini",
                "kark": "cancer", "singh": "leo", "kanya": "virgo",
                "tula": "libra", "vrishchik": "scorpio", "dhanu": "sagittarius",
                "makar": "capricorn", "kumbh": "aquarius", "meen": "pisces"
            }
            return hindi_to_english.get(sign, sign)

    return None


def _extract_time_from_query(query: str) -> Optional[str]:
    """Extract preferred time from query."""
    # Patterns like "7am", "7:00", "7 am", "morning", "evening"
    time_patterns = [
        (r"(\d{1,2})\s*(?::|\.)\s*(\d{2})\s*(am|pm)?", None),
        (r"(\d{1,2})\s*(am|pm)", None),
        (r"morning", "07:00"),
        (r"evening", "18:00"),
        (r"night", "21:00"),
    ]

    query_lower = query.lower()

    for pattern, default_time in time_patterns:
        if default_time:
            if pattern in query_lower:
                return default_time
        else:
            match = re.search(pattern, query_lower)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 1 and groups[1] and groups[1].isdigit() else 0
                ampm = groups[-1] if groups[-1] in ["am", "pm"] else None

                if ampm == "pm" and hour < 12:
                    hour += 12
                elif ampm == "am" and hour == 12:
                    hour = 0

                return f"{hour:02d}:{minute:02d}"

    return None


def _get_planet_emoji(planet: str) -> str:
    """Get emoji for planet."""
    emojis = {
        "sun": "☀️", "moon": "🌙", "mercury": "☿️",
        "venus": "♀️", "mars": "♂️", "jupiter": "♃",
        "saturn": "♄", "rahu": "☊", "ketu": "☋",
    }
    return emojis.get(planet.lower(), "🪐")
