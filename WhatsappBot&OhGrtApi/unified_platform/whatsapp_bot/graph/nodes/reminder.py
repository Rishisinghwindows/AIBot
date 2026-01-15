"""
Reminder Node.

Handles setting and managing reminders.
Supports multilingual responses (11+ Indian languages).
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from common.graph.state import BotState
from common.i18n.responses import get_reminder_label, get_phrase
from whatsapp_bot.stores.pending_reminder_store import get_pending_reminder_store

logger = logging.getLogger(__name__)

INTENT = "set_reminder"


def parse_time_expression(text: str) -> Optional[Tuple[datetime, str]]:
    """
    Parse time expression from text.

    Args:
        text: User message

    Returns:
        Tuple of (reminder_time, reminder_text) or None
    """
    text_lower = text.lower()
    now = datetime.now()

    # Pattern: "remind me in/after X minutes/hours"
    duration_match = re.search(
        r'(?:in|after)\s+(\d+)\s*(minute|min|hour|hr)s?',
        text_lower
    )
    if duration_match:
        amount = int(duration_match.group(1))
        unit = duration_match.group(2)

        if unit in ("minute", "min"):
            reminder_time = now + timedelta(minutes=amount)
        else:
            reminder_time = now + timedelta(hours=amount)

        # Extract what to remind about
        reminder_text = re.sub(
            r'(?:set\s+a\s+reminder\s*(?:for|to)?|remind\s*me\s*(?:to|for)?|in\s+\d+\s*\w+|after\s+\d+\s*\w+)',
            '',
            text_lower
        ).strip()

        return reminder_time, reminder_text or "Reminder"

    # Pattern: "remind me at/for/in X pm" or "set it for 6:05 pm"
    time_match = re.search(
        r'(?:\b(?:at|for|by|around|on|in)\b\s*)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b',
        text_lower
    )
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        period = time_match.group(3)

        if period == "pm" and hour < 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0

        reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If time is in the past, schedule for tomorrow
        if reminder_time < now:
            reminder_time += timedelta(days=1)

        time_phrase = time_match.group(0)
        reminder_text = text_lower.replace(time_phrase, "")
        reminder_text = re.sub(
            r'(?:set\s*(?:a\s*)?reminder|remind\s*me|set\s*it)\s*(?:for|to|about)?',
            '',
            reminder_text
        ).strip()

        return reminder_time, reminder_text or "Reminder"

    # Pattern: 24-hour time like "18:05" (assume today if in future)
    time_match_24h = re.search(
        r'(?:\b(?:at|for|by|around|on|in)\b\s*)?([01]?\d|2[0-3]):([0-5]\d)\b',
        text_lower
    )
    if time_match_24h:
        hour = int(time_match_24h.group(1))
        minute = int(time_match_24h.group(2))

        reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if reminder_time < now:
            reminder_time += timedelta(days=1)

        time_phrase = time_match_24h.group(0)
        reminder_text = text_lower.replace(time_phrase, "")
        reminder_text = re.sub(
            r'(?:set\s*(?:a\s*)?reminder|remind\s*me|set\s*it)\s*(?:for|to|about)?',
            '',
            reminder_text
        ).strip()

        return reminder_time, reminder_text or "Reminder"

    # Pattern: "remind me tomorrow"
    if "tomorrow" in text_lower:
        reminder_time = now + timedelta(days=1)
        reminder_time = reminder_time.replace(hour=9, minute=0, second=0, microsecond=0)

        reminder_text = re.sub(
            r'remind\s*me\s*(to\s*)?|tomorrow',
            '',
            text_lower
        ).strip()

        return reminder_time, reminder_text or "Reminder"

    return None


async def handle_reminder(state: BotState) -> Dict:
    """
    Handle reminder setting requests.
    Returns response in user's detected language.

    Args:
        state: Current bot state

    Returns:
        State update
    """
    query = state.get("current_query", "")
    whatsapp_message = state.get("whatsapp_message", {})
    user_phone = whatsapp_message.get("from_number", "") or state.get("user_phone", "")
    detected_lang = state.get("detected_language", "en")

    pending_store = get_pending_reminder_store()
    pending = await pending_store.peek_pending(user_phone) if user_phone else None

    # Parse the time expression
    parsed = parse_time_expression(query)

    if pending:
        pending_text = (pending.get("reminder_text") or "").strip()

        if parsed:
            reminder_time, reminder_text = parsed
            if pending_text:
                reminder_text = pending_text
            await pending_store.clear_pending(user_phone)
            parsed = (reminder_time, reminder_text)
        else:
            if pending_text:
                when_to_remind = get_reminder_label("when_to_remind", detected_lang)
                return {
                    "response_text": when_to_remind,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                    "route_log": state.get("route_log", []) + ["reminder:missing_time"],
                }

            if query:
                await pending_store.save_pending(user_phone, query)
                when_to_remind = get_reminder_label("when_to_remind", detected_lang)
                return {
                    "response_text": when_to_remind,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                    "route_log": state.get("route_log", []) + ["reminder:missing_time"],
                }

    if not parsed:
        if user_phone:
            await pending_store.save_pending(user_phone, "")
        what_to_remind = get_reminder_label("what_to_remind", detected_lang)
        return {
            "response_text": what_to_remind,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "route_log": state.get("route_log", []) + ["reminder:missing_time"],
        }

    reminder_time, reminder_text = parsed

    try:
        from whatsapp_bot.services.reminder_service import create_reminder

        reminder = await create_reminder(
            phone=user_phone,
            text=reminder_text,
            time=reminder_time,
        )

        time_str = reminder_time.strftime("%I:%M %p on %B %d")
        success_msg = get_reminder_label("set_success", detected_lang)
        will_remind = get_reminder_label("will_remind", detected_lang, when=time_str)

        response = (
            f"✅ {success_msg}\n\n"
            f"*{reminder_text}*\n"
            f"📅 {will_remind}"
        )

        return {
            "response_text": response,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "tool_result": {
                "reminder_time": reminder_time.isoformat(),
                "reminder_text": reminder_text,
            },
            "route_log": state.get("route_log", []) + ["reminder:created"],
        }

    except Exception as e:
        logger.error(f"Reminder creation error: {e}")
        error_msg = get_reminder_label("error", detected_lang)
        return {
            "response_text": error_msg,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": str(e),
            "route_log": state.get("route_log", []) + ["reminder:error"],
        }
