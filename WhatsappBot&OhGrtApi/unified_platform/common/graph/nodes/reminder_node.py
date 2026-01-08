"""
Reminder Node

Handles setting reminders for the user.
"""

import re
from common.graph.state import BotState
from common.tools.reminder_tool import set_reminder


def _extract_reminder_details(query: str) -> tuple[str, str]:
    """
    Extract time and message from reminder query.

    Examples:
    - "Remind me in 5 minutes to call mom" -> ("5 minutes", "call mom")
    - "Reminder in 1 hour to take medicine" -> ("1 hour", "take medicine")
    - "Set reminder for 3pm to attend meeting" -> ("3pm", "attend meeting")

    Returns:
        Tuple of (time_str, message)
    """
    query_lower = query.lower().strip()

    # Pattern 1: "remind me in X to Y" or "reminder in X to Y"
    pattern1 = r"(?:remind(?:er)?(?:\s+me)?)\s+in\s+(.+?)\s+to\s+(.+?)$"
    match = re.search(pattern1, query_lower)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Pattern 2: "remind me to Y in X" or "reminder to Y in X"
    pattern2 = r"(?:remind(?:er)?(?:\s+me)?)\s+to\s+(.+?)\s+in\s+(.+?)$"
    match = re.search(pattern2, query_lower)
    if match:
        return match.group(2).strip(), match.group(1).strip()

    # Pattern 3: "set reminder for X to Y"
    pattern3 = r"set\s+(?:a\s+)?reminder\s+(?:for\s+)?(.+?)\s+to\s+(.+?)$"
    match = re.search(pattern3, query_lower)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Pattern 4: "remind me at X to Y"
    pattern4 = r"(?:remind(?:er)?(?:\s+me)?)\s+at\s+(.+?)\s+to\s+(.+?)$"
    match = re.search(pattern4, query_lower)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Pattern 5: Simple "remind me to Y" (default to 5 minutes)
    pattern5 = r"(?:remind(?:er)?(?:\s+me)?)\s+to\s+(.+?)$"
    match = re.search(pattern5, query_lower)
    if match:
        return "5 minutes", match.group(1).strip()

    return "", ""


async def handle_reminder(state: BotState) -> dict:
    """
    Node function: Sets a reminder based on user input.

    Args:
        state: Current bot state with extracted entities for reminder time and message.

    Returns:
        Updated state with reminder confirmation or error.
    """
    entities = state.get("extracted_entities", {})
    query = state.get("current_query", "")

    # Try to get from entities first, then extract from query
    time_str = entities.get("reminder_time", "").strip()
    message = entities.get("reminder_message", "").strip()

    if not time_str or not message:
        extracted_time, extracted_message = _extract_reminder_details(query)
        time_str = time_str or extracted_time
        message = message or extracted_message

    from_number = state["whatsapp_message"].get("from_number", "")

    if not time_str or not message:
        return {
            "response_text": (
                "To set a reminder, please tell me the time and the message. "
                "\n\n*Example:* Remind me in 5 minutes to call John."
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": "set_reminder",
        }

    try:
        result = await set_reminder(time_str, message, from_number)

        if result["success"]:
            scheduled_time = result["data"].get("scheduled_time")
            is_demo = result["data"].get("demo_mode", False)

            response = f"✅ *Reminder set!*\n\n⏰ Time: {scheduled_time}\n📝 Message: {message}"
            if is_demo:
                response += "\n\n_Note: Running in demo mode. In production, you'll receive a WhatsApp reminder._"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": "set_reminder",
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"Sorry, I couldn't set the reminder. {result.get('error')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "set_reminder",
            }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": f"An unexpected error occurred while setting the reminder.",
            "response_type": "text",
            "should_fallback": True,
            "intent": "set_reminder",
        }
