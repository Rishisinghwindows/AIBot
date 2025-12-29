#!/usr/bin/env python3
"""
D23Bot CLI Chat Interface

A simple command-line interface to test the bot without WhatsApp.
Useful for local development and testing.

Usage:
    python cli_chat.py          # Uses V1 graph (requires DB)
    python cli_chat.py --v2     # Uses V2 graph (domain-based routing)
    python cli_chat.py --lite   # Run without database checkpointer (no persistence)
"""

import asyncio
import argparse
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 60)
    print("🔮 D23Bot CLI Chat Interface")
    print("=" * 60)
    print("Type your message and press Enter to chat.")
    print("")
    print("Commands:")
    print("  /quit, /exit  - Exit the chat")
    print("  /clear        - Clear conversation (new session)")
    print("  /help         - Show available features")
    print("  /v1           - Switch to V1 graph")
    print("  /v2           - Switch to V2 graph")
    print("  /debug        - Toggle debug mode")
    print("")
    print("Tip: Use --lite flag for testing without PostgreSQL")
    print("=" * 60 + "\n")


def print_help():
    """Print available features."""
    print("\n" + "=" * 50)
    print("📋 D23Bot - Available Features")
    print("=" * 50)

    print("\n🌟 ASTROLOGY")
    print("   • Horoscope: 'Aries horoscope', 'Leo rashifal'")
    print("   • Kundli: 'My kundli for 15-08-1990 10:30 AM Delhi'")
    print("   • Matching: 'Match kundli of Rahul and Priya'")
    print("   • Dosha: 'Check mangal dosha', 'Kaal sarp dosh'")
    print("   • Predictions: 'When will I get married?'")
    print("   • Panchang: 'Today's panchang', 'Shubh muhurat'")
    print("   • Numerology: 'Numerology for Rahul Kumar'")
    print("   • Tarot: 'Tarot reading for career'")

    print("\n🚆 TRAVEL")
    print("   • PNR: 'Check PNR 1234567890'")
    print("   • Train: 'Train 12301 running status'")
    print("   • Metro: 'Metro from Dwarka to Rajiv Chowk'")

    print("\n🛠️ UTILITIES")
    print("   • Weather: 'Weather in Delhi', 'Temperature Mumbai'")
    print("   • News: 'Latest news', 'Today's headlines'")
    print("   • Reminders: 'Remind me in 5 min to call mom'")
    print("   • Images: 'Generate image of a sunset'")
    print("   • Search: 'Restaurants near me'")

    print("\n🎮 GAMES")
    print("   • Word Game: 'Play word game', 'Let's play'")

    print("\n" + "=" * 50 + "\n")


class CLIChat:
    """CLI Chat handler for D23Bot."""

    def __init__(self, use_v2: bool = False, lite_mode: bool = False):
        """Initialize CLI chat."""
        self.use_v2 = use_v2
        self.lite_mode = lite_mode
        self.session_id = str(uuid.uuid4())[:8]
        self.phone_number = f"cli_test_{self.session_id}"
        self.debug = False
        self.process_message = None
        self._graph = None
        self._initialized = False

    async def initialize(self):
        """Initialize the graph (lazy loading)."""
        if self._initialized:
            return

        try:
            if self.lite_mode:
                # Create graph without database checkpointer
                await self._init_lite_mode()
            else:
                # Use full graph with database
                await self._init_full_mode()

            self._initialized = True

        except Exception as e:
            print(f"❌ Error initializing graph: {e}")
            print("💡 Tip: Make sure PostgreSQL is running or use --lite flag")
            raise

    async def _init_lite_mode(self):
        """Initialize graph without database (no persistence)."""
        print("⚠️  Running in lite mode (no conversation persistence)")

        if self.use_v2:
            from bot.graph_v2 import create_graph_v2
            self._graph = create_graph_v2().compile()
            print("✅ Loaded V2 graph (domain-based, lite mode)")
        else:
            from bot.graph import create_graph
            self._graph = create_graph().compile()
            print("✅ Loaded V1 graph (intent-based, lite mode)")

        # Create a wrapper function for lite mode
        async def process_lite(msg: dict) -> dict:
            from bot.state import WhatsAppMessage, create_initial_state
            initial_state = create_initial_state(
                WhatsAppMessage(
                    message_id=msg.get("message_id", ""),
                    from_number=msg.get("from_number", ""),
                    phone_number_id=msg.get("phone_number_id", ""),
                    timestamp=msg.get("timestamp", ""),
                    message_type=msg.get("message_type", "text"),
                    text=msg.get("text"),
                    media_id=msg.get("media_id"),
                )
            )
            result = await self._graph.ainvoke(initial_state)
            return {
                "response_text": result.get("response_text", ""),
                "response_type": result.get("response_type", "text"),
                "response_media_url": result.get("response_media_url"),
                "intent": result.get("intent", "unknown"),
                "domain": result.get("domain", ""),
                "error": result.get("error"),
            }

        self.process_message = process_lite

    async def _init_full_mode(self):
        """Initialize graph with full database support."""
        if self.use_v2:
            from bot.graph_v2 import process_message_v2
            self.process_message = process_message_v2
            print("✅ Loaded V2 graph (domain-based routing)")
        else:
            from bot.graph import process_message
            self.process_message = process_message
            print("✅ Loaded V1 graph (intent-based routing)")

    def create_mock_message(self, text: str) -> dict:
        """Create a mock WhatsApp message."""
        return {
            "message_id": str(uuid.uuid4()),
            "from_number": self.phone_number,
            "phone_number_id": "cli_test_server",
            "timestamp": datetime.now().isoformat(),
            "message_type": "text",
            "text": text,
            "media_id": None,
        }

    async def chat(self, user_input: str) -> str:
        """Process user input and return response."""
        if not self._initialized:
            await self.initialize()

        try:
            mock_message = self.create_mock_message(user_input)

            if self.debug:
                print(f"\n🔍 Debug: Sending message: {mock_message}")

            result = await self.process_message(mock_message)

            if self.debug:
                print(f"🔍 Debug: Full result: {result}")

            response_text = result.get("response_text", "No response")
            intent = result.get("intent", "unknown")
            domain = result.get("domain", "")
            error = result.get("error")

            # Format response
            response = response_text

            if self.debug:
                response += f"\n\n[Intent: {intent}"
                if domain:
                    response += f", Domain: {domain}"
                if error:
                    response += f", Error: {error}"
                response += "]"

            return response

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def switch_graph(self, use_v2: bool):
        """Switch between V1 and V2 graphs."""
        self.use_v2 = use_v2
        self._initialized = False
        self.process_message = None
        self._graph = None

    def clear_session(self):
        """Start a new session."""
        self.session_id = str(uuid.uuid4())[:8]
        self.phone_number = f"cli_test_{self.session_id}"
        print(f"🔄 New session started: {self.session_id}")


async def main():
    """Main CLI loop."""
    parser = argparse.ArgumentParser(description="D23Bot CLI Chat Interface")
    parser.add_argument("--v2", action="store_true", help="Use V2 graph (domain-based)")
    parser.add_argument("--lite", action="store_true", help="Run without database (no persistence)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    print_banner()

    chat = CLIChat(use_v2=args.v2, lite_mode=args.lite)
    chat.debug = args.debug

    # Initialize graph
    try:
        await chat.initialize()
    except Exception:
        print("\n💡 Try running: docker-compose up -d postgres")
        print("   Or use: python cli_chat.py --lite\n")
        return

    print(f"📱 Session ID: {chat.session_id}")
    graph_mode = "V2 (domain-based)" if chat.use_v2 else "V1 (intent-based)"
    if chat.lite_mode:
        graph_mode += " [LITE]"
    print(f"📊 Graph: {graph_mode}")
    print(f"🐛 Debug: {'ON' if chat.debug else 'OFF'}")
    print("")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ["/quit", "/exit"]:
                print("\n👋 Goodbye!")
                break

            elif user_input.lower() == "/clear":
                chat.clear_session()
                continue

            elif user_input.lower() == "/help":
                print_help()
                continue

            elif user_input.lower() == "/v1":
                chat.switch_graph(use_v2=False)
                await chat.initialize()
                print("📊 Switched to V1 graph")
                continue

            elif user_input.lower() == "/v2":
                chat.switch_graph(use_v2=True)
                await chat.initialize()
                print("📊 Switched to V2 graph")
                continue

            elif user_input.lower() == "/debug":
                chat.debug = not chat.debug
                print(f"🐛 Debug mode: {'ON' if chat.debug else 'OFF'}")
                continue

            # Process message
            print("\n⏳ Processing...\n")
            response = await chat.chat(user_input)
            print(f"🤖 Bot: {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())
