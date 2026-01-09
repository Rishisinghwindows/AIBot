"""
Subscription Node.

Handles subscription management for daily horoscope and alerts.
Supports multilingual responses (11+ Indian languages).
"""

import logging
import re
from typing import Dict

from common.graph.state import BotState
from common.i18n.responses import get_subscription_label

logger = logging.getLogger(__name__)

INTENT = "subscription"

# Zodiac sign mappings
ZODIAC_SIGNS = {
    "aries": "aries", "mesh": "aries",
    "taurus": "taurus", "vrishabh": "taurus",
    "gemini": "gemini", "mithun": "gemini",
    "cancer": "cancer", "kark": "cancer",
    "leo": "leo", "singh": "leo",
    "virgo": "virgo", "kanya": "virgo",
    "libra": "libra", "tula": "libra",
    "scorpio": "scorpio", "vrishchik": "scorpio",
    "sagittarius": "sagittarius", "dhanu": "sagittarius",
    "capricorn": "capricorn", "makar": "capricorn",
    "aquarius": "aquarius", "kumbh": "aquarius",
    "pisces": "pisces", "meen": "pisces",
}


def extract_sign(text: str) -> str:
    """Extract zodiac sign from text."""
    text_lower = text.lower()
    for name, sign in ZODIAC_SIGNS.items():
        if name in text_lower:
            return sign
    return ""


def parse_subscription_action(text: str) -> Dict:
    """
    Parse subscription action from text.

    Returns:
        Dict with action (subscribe/unsubscribe/list) and type
    """
    text_lower = text.lower()

    if "unsubscribe" in text_lower or "stop" in text_lower:
        action = "unsubscribe"
    elif "subscribe" in text_lower:
        action = "subscribe"
    elif "my subscription" in text_lower or "list" in text_lower:
        action = "list"
    else:
        action = "info"

    sub_type = "horoscope"  # Default
    if "transit" in text_lower:
        sub_type = "transit"
    elif "reminder" in text_lower:
        sub_type = "reminder"

    return {"action": action, "type": sub_type}


async def handle_subscription(state: BotState) -> Dict:
    """
    Handle subscription management.
    Returns response in user's detected language.

    Args:
        state: Current bot state

    Returns:
        State update
    """
    query = state.get("current_query", "")
    user_phone = state.get("user_phone", "")
    detected_lang = state.get("detected_language", "en")

    # Parse the subscription action
    action_info = parse_subscription_action(query)
    action = action_info["action"]
    sub_type = action_info["type"]

    if action == "info":
        # Show subscription options (localized)
        title = get_subscription_label("title", detected_lang)
        daily_horoscope = get_subscription_label("daily_horoscope", detected_lang)
        transit_alerts = get_subscription_label("transit_alerts", detected_lang)

        response = (
            f"*{title}:*\n\n"
            f"• *{daily_horoscope}*\n"
            "  `subscribe horoscope <sign>`\n\n"
            f"• *{transit_alerts}*\n"
            "  `subscribe transit`"
        )

        return {
            "response_text": response,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "route_log": state.get("route_log", []) + ["subscription:info"],
        }

    if action == "list":
        # List user's subscriptions
        try:
            from whatsapp_bot.services.subscription_service import get_user_subscriptions
            subscriptions = await get_user_subscriptions(user_phone)

            if not subscriptions:
                response = get_subscription_label("no_subscriptions", detected_lang)
            else:
                your_subs = get_subscription_label("your_subscriptions", detected_lang)
                lines = [f"*{your_subs}:*", ""]
                for sub in subscriptions:
                    lines.append(f"• {sub['type'].title()}: {sub.get('details', 'Active')}")
                response = "\n".join(lines)

            return {
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
                "route_log": state.get("route_log", []) + ["subscription:list"],
            }
        except Exception as e:
            logger.error(f"Error listing subscriptions: {e}")
            error_msg = get_subscription_label("error", detected_lang)
            return {
                "response_text": error_msg,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    if action == "subscribe":
        if sub_type == "horoscope":
            # Need to extract zodiac sign
            sign = extract_sign(query)
            if not sign:
                response = get_subscription_label("specify_sign", detected_lang)
                return {
                    "response_text": response,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                }

            try:
                from whatsapp_bot.services.subscription_service import subscribe_horoscope
                await subscribe_horoscope(user_phone, sign)

                subscribed = get_subscription_label("subscribed", detected_lang)
                daily_horoscope = get_subscription_label("daily_horoscope", detected_lang)
                response = f"✅ {subscribed}\n\n*{sign.title()}* - {daily_horoscope}"

                return {
                    "response_text": response,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                    "route_log": state.get("route_log", []) + ["subscription:subscribed"],
                }
            except Exception as e:
                logger.error(f"Subscription error: {e}")
                error_msg = get_subscription_label("error", detected_lang)
                return {
                    "response_text": error_msg,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                }

        elif sub_type == "transit":
            try:
                from whatsapp_bot.services.subscription_service import subscribe_transit
                await subscribe_transit(user_phone)

                subscribed = get_subscription_label("subscribed", detected_lang)
                transit_alerts = get_subscription_label("transit_alerts", detected_lang)
                response = f"✅ {subscribed}\n\n{transit_alerts}"

                return {
                    "response_text": response,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                }
            except Exception as e:
                logger.error(f"Transit subscription error: {e}")
                error_msg = get_subscription_label("error", detected_lang)
                return {
                    "response_text": error_msg,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                }

    if action == "unsubscribe":
        try:
            from whatsapp_bot.services.subscription_service import unsubscribe
            await unsubscribe(user_phone, sub_type)

            unsubscribed = get_subscription_label("unsubscribed", detected_lang)
            response = f"✅ {unsubscribed} - *{sub_type.title()}*"

            return {
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
                "route_log": state.get("route_log", []) + ["subscription:unsubscribed"],
            }
        except Exception as e:
            logger.error(f"Unsubscribe error: {e}")
            error_msg = get_subscription_label("error", detected_lang)
            return {
                "response_text": error_msg,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    error_msg = get_subscription_label("error", detected_lang)
    return {
        "response_text": error_msg,
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }
