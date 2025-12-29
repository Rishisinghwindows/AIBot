"""
D23Bot Chainlit Web Interface

A multilingual web-based chat interface for testing the bot.
Supports 22 Indian languages with intelligent conversation flows.

Features:
- Multi-turn conversations (step-based birth detail collection)
- Follow-up question handling
- Language auto-detection (Hindi, Bengali, Tamil, etc.)
- Lite mode (no database required)

Usage:
    # Lite mode (recommended for testing)
    LITE_MODE=true chainlit run chainlit_app.py -w --port 8000

    # Full mode (requires PostgreSQL)
    chainlit run chainlit_app.py -w --port 8000

Or with Docker:
    docker-compose --profile dev up chainlit
"""

import os
import sys
import re

# CRITICAL: Add project root to Python path BEFORE any other imports
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
os.chdir(_PROJECT_ROOT)  # Also change working directory

import uuid
from datetime import datetime
from typing import Optional, Dict

import chainlit as cl
from dotenv import load_dotenv


def _parse_location_input(text: str) -> Optional[Dict]:
    """
    Parse location input from user.

    Supports formats:
    - "28.6139, 77.2090" (lat, lon)
    - "28.6139 77.2090" (lat lon)
    - "Delhi" or "Connaught Place Delhi" (place name - will be used as address)

    Returns:
        Location dict with latitude, longitude, name, address or None
    """
    text = text.strip()

    # Try to parse as coordinates (lat, lon)
    # Pattern: number, number or number number
    coord_pattern = r'^(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)$'
    match = re.match(coord_pattern, text)
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            # Validate reasonable lat/lon ranges
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "name": f"Location ({lat}, {lon})",
                    "address": None,
                }
        except ValueError:
            pass

    # Treat as place name/address
    if len(text) > 2:
        return {
            "latitude": 0,  # Will be ignored, address is used
            "longitude": 0,
            "name": text,
            "address": text,
        }

    return None

# Load environment variables
load_dotenv(dotenv_path=os.path.join(_PROJECT_ROOT, ".env"))

# Configuration
LITE_MODE = os.getenv("LITE_MODE", "true").lower() == "true"
USE_V2 = True

# Initialize graph based on mode
_graph = None
_process_message = None


def _init_graph():
    """Initialize graph (lazy loading)."""
    global _graph, _process_message

    if _process_message is not None:
        return

    # Debug: ensure path is correct
    import sys
    import os
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    print(f"DEBUG: sys.path[0] = {sys.path[0]}")
    print(f"DEBUG: project_root = {project_root}")
    print(f"DEBUG: bot exists = {os.path.exists(os.path.join(project_root, 'bot'))}")

    if LITE_MODE:
        # Lite mode - no database checkpointer
        print("Starting in LITE mode (no database persistence)")
        try:
            from bot.graph_v2 import create_graph_v2
            from bot.state import WhatsAppMessage, create_initial_state

            _graph = create_graph_v2().compile()

            async def process_lite(msg: dict) -> dict:
                initial_state = create_initial_state(
                    WhatsAppMessage(
                        message_id=msg.get("message_id", ""),
                        from_number=msg.get("from_number", ""),
                        phone_number_id=msg.get("phone_number_id", ""),
                        timestamp=msg.get("timestamp", ""),
                        message_type=msg.get("message_type", "text"),
                        text=msg.get("text"),
                        media_id=msg.get("media_id"),
                        location=msg.get("location"),
                    )
                )
                result = await _graph.ainvoke(initial_state)
                return {
                    "response_text": result.get("response_text", ""),
                    "response_type": result.get("response_type", "text"),
                    "response_media_url": result.get("response_media_url"),
                    "intent": result.get("intent", "unknown"),
                    "domain": result.get("domain", ""),
                    "error": result.get("error"),
                }

            _process_message = process_lite
            print("V2 graph loaded (lite mode)")

        except Exception as e:
            print(f"Error loading V2 graph: {e}")
            # Fallback to V1
            from bot.graph import create_graph
            from bot.state import WhatsAppMessage, create_initial_state

            _graph = create_graph().compile()

            async def process_lite_v1(msg: dict) -> dict:
                initial_state = create_initial_state(
                    WhatsAppMessage(
                        message_id=msg.get("message_id", ""),
                        from_number=msg.get("from_number", ""),
                        phone_number_id=msg.get("phone_number_id", ""),
                        timestamp=msg.get("timestamp", ""),
                        message_type=msg.get("message_type", "text"),
                        text=msg.get("text"),
                        media_id=msg.get("media_id"),
                        location=msg.get("location"),
                    )
                )
                result = await _graph.ainvoke(initial_state)
                return {
                    "response_text": result.get("response_text", ""),
                    "response_type": result.get("response_type", "text"),
                    "response_media_url": result.get("response_media_url"),
                    "intent": result.get("intent", "unknown"),
                    "domain": result.get("domain", ""),
                    "error": result.get("error"),
                }

            _process_message = process_lite_v1
            print("V1 graph loaded (lite mode)")
    else:
        # Full mode with database
        try:
            from bot.graph_v2 import process_message_v2
            _process_message = process_message_v2
            print("V2 graph loaded (full mode)")
        except ImportError:
            from bot.graph import process_message
            _process_message = process_message
            print("V1 graph loaded (full mode)")


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session."""
    # Initialize graph on first chat
    _init_graph()

    # Create unique session ID
    session_id = str(uuid.uuid4())[:8]

    # Store in user session
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("phone_number", f"chainlit_{session_id}")

    # Welcome message
    mode_info = "V2" if USE_V2 else "V1"
    if LITE_MODE:
        mode_info += " (lite)"

    await cl.Message(
        content=f"""**Welcome to D23Bot!**

Your AI-powered assistant for astrology, travel, and more - in **22 Indian languages**!

---

**ASTROLOGY**
• *Horoscope:* "Aries horoscope" | "मेष राशिफल" | "মেষ রাশিফল"
• *Kundli:* "My kundli for 15-08-1990 10:30 AM Delhi"
• *Matching:* "Match kundli of Rahul and Priya"
• *Dosha:* "Check mangal dosha" | "मांगलिक दोष चेक करो"
• *Predictions:* "When will I get married?" | "मेरी शादी कब होगी?"
• *Panchang:* "Today's panchang" | "आज का पंचांग"

**TRAVEL**
• *PNR:* "Check PNR 1234567890"
• *Train:* "Train 12301 running status"
• *Metro:* "Metro from Dwarka to Rajiv Chowk"

**UTILITIES**
• *Weather:* "Weather in Delhi" | "दिल्ली में मौसम"
• *News:* "Latest news" | "ताज़ा खबर"
• *Image:* "Generate image of a sunset"

---

**Multi-turn Conversations Supported:**
Just ask "When will I get married?" and I'll guide you through providing your birth details step by step.

**Follow-up Questions Work:**
After a prediction, ask "What about career?" or "aur batao" to continue.

---

_Supports: Hindi, Bengali, Tamil, Telugu, Gujarati, Marathi + 16 more_
_Session: {session_id} | {mode_info}_
"""
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Process incoming messages."""
    # Ensure graph is initialized
    _init_graph()

    session_id = cl.user_session.get("session_id")
    phone_number = cl.user_session.get("phone_number")

    # Check if user is responding to a location request
    pending_location = cl.user_session.get("pending_location_request")
    location_data = None
    message_type = "text"
    text_content = message.content

    if pending_location:
        # User is providing location - parse it
        location_data = _parse_location_input(message.content)
        if location_data:
            message_type = "location"
            text_content = None
            cl.user_session.set("pending_location_request", None)  # Clear pending

    # Create mock WhatsApp message
    mock_message = {
        "message_id": str(uuid.uuid4()),
        "from_number": phone_number,
        "phone_number_id": "chainlit_server",
        "timestamp": datetime.now().isoformat(),
        "message_type": message_type,
        "text": text_content,
        "media_id": None,
        "location": location_data,
    }

    # Show thinking indicator
    msg = cl.Message(content="")
    await msg.send()

    try:
        # Process through bot graph
        result = await _process_message(mock_message)

        response_text = result.get("response_text", "No response")
        response_type = result.get("response_type", "text")
        response_media_url = result.get("response_media_url")
        intent = result.get("intent", "unknown")
        domain = result.get("domain", "")
        error = result.get("error")

        # Build response with metadata
        elements = []

        # Handle location request - ask user to provide location
        if response_type == "location_request":
            cl.user_session.set("pending_location_request", True)
            location_prompt = (
                f"{response_text}\n\n"
                "---\n"
                "**Please provide your location:**\n"
                "- Enter a place name (e.g., `Connaught Place Delhi`)\n"
                "- Or enter coordinates (e.g., `28.6139, 77.2090`)\n"
            )
            msg.content = location_prompt
            await msg.update()
            return

        # Add image if present
        if response_type == "image" and response_media_url:
            elements.append(
                cl.Image(
                    url=response_media_url,
                    name="generated_image",
                    display="inline"
                )
            )

        # Add metadata footer
        metadata = f"\n\n---\n_Intent: {intent}"
        if domain:
            metadata += f" | Domain: {domain}"
        if error:
            metadata += f" | ⚠️ Error: {error}"
        metadata += "_"

        # Update message with response
        msg.content = response_text + metadata
        msg.elements = elements
        await msg.update()

    except Exception as e:
        msg.content = f"❌ **Error:** {str(e)}\n\nPlease try again."
        await msg.update()


@cl.on_chat_end
async def on_chat_end():
    """Clean up on chat end."""
    session_id = cl.user_session.get("session_id")
    print(f"Chat ended for session: {session_id}")


# Optional: Add action buttons
@cl.action_callback("horoscope")
async def on_horoscope_action(action: cl.Action):
    """Quick action for horoscope."""
    await on_message(cl.Message(content="What's today's horoscope for Aries?"))


@cl.action_callback("weather")
async def on_weather_action(action: cl.Action):
    """Quick action for weather."""
    await on_message(cl.Message(content="Weather in Delhi"))


# Run configuration
if __name__ == "__main__":
    print("Run with: chainlit run chainlit_app.py -w --port 8000")
