#!/usr/bin/env python3
"""
D23Bot Logic Validation Script

Tests various bot intents and responses.
Supports both V1 (intent-based) and V2 (domain-based) graphs.

Usage:
    python test_bot_logic.py          # Test V1 graph
    python test_bot_logic.py --v2     # Test V2 graph
    python test_bot_logic.py --quick  # Quick test (fewer cases)
"""

import asyncio
import argparse
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test cases organized by domain
TEST_CASES = {
    "astrology": [
        {
            "input": "Aries horoscope",
            "category": "Horoscope",
            "expected_intent": "get_horoscope",
            "expected_domain": "astrology",
        },
        {
            "input": "Kundli for Rahul born on 15-08-1990 at 10:30 AM in Delhi",
            "category": "Birth Chart",
            "expected_intent": "birth_chart",
            "expected_domain": "astrology",
        },
        {
            "input": "Match kundli of Rahul (15-08-1990) and Priya (22-03-1992)",
            "category": "Matching",
            "expected_intent": "kundli_matching",
            "expected_domain": "astrology",
        },
        {
            "input": "Numerology for Rahul Kumar",
            "category": "Numerology",
            "expected_intent": "numerology",
            "expected_domain": "astrology",
        },
        {
            "input": "Tarot reading for my career",
            "category": "Tarot",
            "expected_intent": "tarot_reading",
            "expected_domain": "astrology",
        },
        {
            "input": "What does Saturn return mean?",
            "category": "Ask Astrologer",
            "expected_intent": "ask_astrologer",
            "expected_domain": "astrology",
        },
        {
            "input": "Check mangal dosha for 15-08-1990",
            "category": "Dosha Check",
            "expected_intent": "dosha_check",
            "expected_domain": "astrology",
        },
        {
            "input": "Life prediction for career",
            "category": "Life Prediction",
            "expected_intent": "life_prediction",
            "expected_domain": "astrology",
        },
        {
            "input": "Today's panchang",
            "category": "Panchang",
            "expected_intent": "get_panchang",
            "expected_domain": "astrology",
        },
    ],
    "travel": [
        {
            "input": "Check PNR 1234567890",
            "category": "PNR Status",
            "expected_intent": "pnr_status",
            "expected_domain": "travel",
        },
        {
            "input": "Train 12301 status",
            "category": "Train Status",
            "expected_intent": "train_status",
            "expected_domain": "travel",
        },
        {
            "input": "Metro from Dwarka to Rajiv Chowk",
            "category": "Metro",
            "expected_intent": "metro_ticket",
            "expected_domain": "travel",
        },
    ],
    "utility": [
        {
            "input": "Restaurants near me",
            "category": "Local Search",
            "expected_intent": "local_search",
            "expected_domain": "utility",
        },
        {
            "input": "Generate image of a futuristic indian city",
            "category": "Image Gen",
            "expected_intent": "image",
            "expected_domain": "utility",
        },
        {
            "input": "Weather in Mumbai",
            "category": "Weather",
            "expected_intent": "weather",
            "expected_domain": "utility",
        },
        {
            "input": "Latest news",
            "category": "News",
            "expected_intent": "get_news",
            "expected_domain": "utility",
        },
        {
            "input": "Remind me in 5 minutes to drink water",
            "category": "Reminder",
            "expected_intent": "set_reminder",
            "expected_domain": "utility",
        },
    ],
    "game": [
        {
            "input": "Play a game",
            "category": "Word Game",
            "expected_intent": "word_game",
            "expected_domain": "game",
        },
    ],
    "conversation": [
        {
            "input": "Hello, how are you?",
            "category": "Greeting",
            "expected_intent": "chat",
            "expected_domain": "conversation",
        },
        {
            "input": "What can you do?",
            "category": "Help",
            "expected_intent": "chat",
            "expected_domain": "conversation",
        },
    ],
    "subscription": [
        {
            "input": "Subscribe horoscope aries",
            "category": "Subscribe Horoscope",
            "expected_intent": "subscription",
            "expected_domain": "utility",
        },
        {
            "input": "Subscribe daily horoscope leo at 7am",
            "category": "Subscribe with Time",
            "expected_intent": "subscription",
            "expected_domain": "utility",
        },
        {
            "input": "Subscribe transit alerts",
            "category": "Subscribe Transit",
            "expected_intent": "subscription",
            "expected_domain": "utility",
        },
        {
            "input": "Unsubscribe horoscope",
            "category": "Unsubscribe Horoscope",
            "expected_intent": "subscription",
            "expected_domain": "utility",
        },
        {
            "input": "Stop daily horoscope",
            "category": "Stop Horoscope",
            "expected_intent": "subscription",
            "expected_domain": "utility",
        },
        {
            "input": "My subscriptions",
            "category": "View Subscriptions",
            "expected_intent": "subscription",
            "expected_domain": "utility",
        },
        {
            "input": "Upcoming planetary transits",
            "category": "View Transits",
            "expected_intent": "subscription",
            "expected_domain": "utility",
        },
        {
            "input": "Subscribe horoscope mesh",
            "category": "Subscribe Hindi Sign",
            "expected_intent": "subscription",
            "expected_domain": "utility",
        },
    ],
}

# Quick test subset
QUICK_TEST_CASES = {
    "astrology": [TEST_CASES["astrology"][0]],  # Horoscope
    "travel": [TEST_CASES["travel"][0]],  # PNR
    "utility": [TEST_CASES["utility"][2]],  # Weather
    "game": [TEST_CASES["game"][0]],  # Word game
    "conversation": [TEST_CASES["conversation"][0]],  # Greeting
    "subscription": [TEST_CASES["subscription"][0]],  # Subscribe Horoscope
}


class TestRunner:
    """Test runner for D23Bot."""

    def __init__(self, use_v2: bool = False):
        """Initialize test runner."""
        self.use_v2 = use_v2
        self.process_message = None
        self.results = {"passed": 0, "failed": 0, "warnings": 0}

    async def initialize(self):
        """Initialize the graph."""
        try:
            if self.use_v2:
                from bot.graph_v2 import process_message_v2
                self.process_message = process_message_v2
                print("Using V2 graph (domain-based routing)")
            else:
                from bot.graph import process_message
                self.process_message = process_message
                print("Using V1 graph (intent-based routing)")
        except Exception as e:
            print(f"Error initializing graph: {e}")
            raise

    def create_mock_message(self, text: str) -> dict:
        """Create a mock WhatsApp message."""
        return {
            "message_id": str(uuid.uuid4()),
            "from_number": f"test_user_{uuid.uuid4().hex[:8]}",
            "phone_number_id": "test_server",
            "timestamp": datetime.now().isoformat(),
            "message_type": "text",
            "text": text,
            "media_id": None,
        }

    async def run_test(self, test_case: dict) -> dict:
        """Run a single test case."""
        input_text = test_case["input"]
        category = test_case["category"]
        expected_intent = test_case.get("expected_intent")
        expected_domain = test_case.get("expected_domain")

        print(f"\n{'─' * 50}")
        print(f"Category: {category}")
        print(f"Input: {input_text}")

        try:
            mock_message = self.create_mock_message(input_text)
            result = await self.process_message(mock_message)

            # Extract results
            intent = result.get("intent", "unknown")
            domain = result.get("domain", "")
            response_text = result.get("response_text", "")
            error = result.get("error")

            # Validation
            status = "PASS"
            issues = []

            if error:
                status = "FAIL"
                issues.append(f"Error: {error}")

            if expected_intent and intent != expected_intent:
                status = "WARN" if status == "PASS" else status
                issues.append(f"Expected intent '{expected_intent}', got '{intent}'")

            if self.use_v2 and expected_domain and domain != expected_domain:
                status = "WARN" if status == "PASS" else status
                issues.append(f"Expected domain '{expected_domain}', got '{domain}'")

            if not response_text:
                status = "WARN" if status == "PASS" else status
                issues.append("Empty response")

            # Print result
            status_icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}[status]
            print(f"Status: {status_icon} {status}")
            print(f"Intent: {intent}" + (f" | Domain: {domain}" if domain else ""))
            print(f"Response: {response_text[:100]}..." if len(response_text) > 100 else f"Response: {response_text}")

            if issues:
                for issue in issues:
                    print(f"  └─ {issue}")

            # Update results
            if status == "PASS":
                self.results["passed"] += 1
            elif status == "FAIL":
                self.results["failed"] += 1
            else:
                self.results["warnings"] += 1

            return {"status": status, "issues": issues}

        except Exception as e:
            print(f"Status: ❌ CRITICAL ERROR")
            print(f"Error: {str(e)}")
            self.results["failed"] += 1
            return {"status": "FAIL", "issues": [str(e)]}

    async def run_all_tests(self, test_cases: dict, delay: float = 1.0):
        """Run all test cases."""
        total = sum(len(cases) for cases in test_cases.values())

        print("\n" + "=" * 60)
        print("D23Bot Logic Validation")
        print("=" * 60)
        print(f"Graph: {'V2 (domain-based)' if self.use_v2 else 'V1 (intent-based)'}")
        print(f"Total Test Cases: {total}")
        print("=" * 60)

        for domain, cases in test_cases.items():
            print(f"\n{'═' * 60}")
            print(f"DOMAIN: {domain.upper()}")
            print(f"{'═' * 60}")

            for test_case in cases:
                await self.run_test(test_case)
                await asyncio.sleep(delay)  # Rate limiting

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✅ Passed:   {self.results['passed']}")
        print(f"⚠️  Warnings: {self.results['warnings']}")
        print(f"❌ Failed:   {self.results['failed']}")
        print(f"Total:      {total}")
        print("=" * 60)

        if self.results["failed"] == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {self.results['failed']} test(s) failed")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="D23Bot Logic Validation")
    parser.add_argument("--v2", action="store_true", help="Use V2 graph")
    parser.add_argument("--quick", action="store_true", help="Run quick test (fewer cases)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between tests (seconds)")
    parser.add_argument("--domain", type=str, help="Test specific domain only")
    args = parser.parse_args()

    runner = TestRunner(use_v2=args.v2)
    await runner.initialize()

    # Select test cases
    test_cases = QUICK_TEST_CASES if args.quick else TEST_CASES

    # Filter by domain if specified
    if args.domain:
        if args.domain in test_cases:
            test_cases = {args.domain: test_cases[args.domain]}
        else:
            print(f"Unknown domain: {args.domain}")
            print(f"Available: {', '.join(test_cases.keys())}")
            return

    await runner.run_all_tests(test_cases, delay=args.delay)


if __name__ == "__main__":
    asyncio.run(main())
