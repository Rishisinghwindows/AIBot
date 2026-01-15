"""
e-Challan Node

Returns official Parivahan e-Challan portal link and steps.
"""

from common.graph.state import BotState
from common.i18n.responses import get_echallan_label

INTENT = "echallan"


def handle_echallan(state: BotState) -> dict:
    detected_lang = state.get("detected_language", "en")
    message = get_echallan_label("message", detected_lang)
    return {
        "response_text": message,
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }
