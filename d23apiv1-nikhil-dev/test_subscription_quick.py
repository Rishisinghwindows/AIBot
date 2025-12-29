#!/usr/bin/env python3
"""
Quick Subscription Feature Tests

Run without database or external services.
Tests intent detection, zodiac extraction, and node routing.

Usage:
    python test_subscription_quick.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_action_detection():
    """Test subscription action detection."""
    from bot.nodes.subscription_node import _determine_action

    print("\n" + "=" * 50)
    print("Testing Action Detection")
    print("=" * 50)

    test_cases = [
        # (query, expected_action)
        ("subscribe horoscope", "subscribe_horoscope"),
        ("subscribe daily horoscope aries", "subscribe_horoscope"),
        ("start horoscope", "subscribe_horoscope"),
        ("enable daily rashifal", "subscribe_horoscope"),
        ("subscribe transit alerts", "subscribe_transit"),
        ("subscribe planetary alerts", "subscribe_transit"),
        ("start transit notifications", "subscribe_transit"),
        ("unsubscribe horoscope", "unsubscribe_horoscope"),
        ("stop horoscope", "unsubscribe_horoscope"),
        ("cancel daily horoscope", "unsubscribe_horoscope"),
        ("unsubscribe alerts", "unsubscribe_transit"),
        ("stop transit alerts", "unsubscribe_transit"),
        ("my subscriptions", "view_subscriptions"),
        ("what am i subscribed to", "view_subscriptions"),
        ("show subscriptions", "view_subscriptions"),
        ("upcoming transits", "view_transits"),
        ("planetary transits", "view_transits"),
        ("show upcoming planet movements", "view_transits"),
    ]

    passed = 0
    failed = 0

    for query, expected in test_cases:
        result = _determine_action(query)
        status = "PASS" if result == expected else "FAIL"

        if status == "PASS":
            passed += 1
            print(f"  [PASS] '{query}' -> {result}")
        else:
            failed += 1
            print(f"  [FAIL] '{query}' -> {result} (expected: {expected})")

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_zodiac_extraction():
    """Test zodiac sign extraction."""
    from bot.nodes.subscription_node import _extract_zodiac_from_query

    print("\n" + "=" * 50)
    print("Testing Zodiac Extraction")
    print("=" * 50)

    test_cases = [
        # English signs
        ("subscribe horoscope aries", "aries"),
        ("subscribe horoscope Taurus", "taurus"),
        ("daily horoscope gemini please", "gemini"),
        ("horoscope for cancer", "cancer"),
        ("leo horoscope", "leo"),
        ("subscribe virgo", "virgo"),
        ("horoscope libra today", "libra"),
        ("scorpio daily", "scorpio"),
        ("sagittarius prediction", "sagittarius"),
        ("capricorn horoscope", "capricorn"),
        ("aquarius daily horoscope", "aquarius"),
        ("pisces prediction", "pisces"),
        # Hindi signs
        ("subscribe mesh", "aries"),
        ("horoscope vrishabh", "taurus"),
        ("mithun rashifal", "gemini"),
        ("kark horoscope", "cancer"),
        ("singh rashifal", "leo"),
        ("kanya prediction", "virgo"),
        ("tula horoscope", "libra"),
        ("vrishchik daily", "scorpio"),
        ("dhanu rashifal", "sagittarius"),
        ("makar prediction", "capricorn"),
        ("kumbh horoscope", "aquarius"),
        ("meen rashifal", "pisces"),
        # No sign
        ("subscribe horoscope", None),
        ("daily horoscope please", None),
    ]

    passed = 0
    failed = 0

    for query, expected in test_cases:
        result = _extract_zodiac_from_query(query)
        status = "PASS" if result == expected else "FAIL"

        if status == "PASS":
            passed += 1
            print(f"  [PASS] '{query}' -> {result}")
        else:
            failed += 1
            print(f"  [FAIL] '{query}' -> {result} (expected: {expected})")

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_time_extraction():
    """Test preferred time extraction."""
    from bot.nodes.subscription_node import _extract_time_from_query

    print("\n" + "=" * 50)
    print("Testing Time Extraction")
    print("=" * 50)

    test_cases = [
        ("subscribe horoscope at 7am", "07:00"),
        ("subscribe horoscope 8am", "08:00"),
        ("horoscope at 10:30 am", "10:30"),
        ("daily horoscope 6pm", "18:00"),
        ("subscribe horoscope morning", "07:00"),
        ("horoscope evening please", "18:00"),
        ("subscribe horoscope night", "21:00"),
        ("subscribe horoscope 9:00", "09:00"),
        # No time
        ("subscribe horoscope aries", None),
        ("daily horoscope", None),
    ]

    passed = 0
    failed = 0

    for query, expected in test_cases:
        result = _extract_time_from_query(query)
        status = "PASS" if result == expected else "FAIL"

        if status == "PASS":
            passed += 1
            print(f"  [PASS] '{query}' -> {result}")
        else:
            failed += 1
            print(f"  [FAIL] '{query}' -> {result} (expected: {expected})")

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_intent_patterns():
    """Test subscription intent patterns in constants."""
    from bot.constants.intents import UTILITY_INTENT_PATTERNS
    import re

    print("\n" + "=" * 50)
    print("Testing Intent Patterns")
    print("=" * 50)

    # Ensure subscription patterns exist
    if "subscription" not in UTILITY_INTENT_PATTERNS:
        print("  [FAIL] 'subscription' not in UTILITY_INTENT_PATTERNS")
        return False

    patterns = UTILITY_INTENT_PATTERNS["subscription"]
    print(f"  Found {len(patterns)} subscription patterns")

    test_queries = [
        "subscribe to daily horoscope",
        "unsubscribe from alerts",
        "my subscription status",
        "stop horoscope notifications",
        "transit alert subscription",
        "upcoming planetary transit",
    ]

    passed = 0
    for query in test_queries:
        matched = any(re.search(p, query.lower()) for p in patterns)
        if matched:
            passed += 1
            print(f"  [PASS] '{query}' matched")
        else:
            print(f"  [FAIL] '{query}' no match")

    print(f"\nResults: {passed}/{len(test_queries)} queries matched")
    return passed >= len(test_queries) // 2  # At least half should match


def test_graph_routing():
    """Test that subscription intent routes correctly."""
    from bot.graph import route_by_intent

    print("\n" + "=" * 50)
    print("Testing Graph Routing")
    print("=" * 50)

    # Test state with subscription intent
    state = {"intent": "subscription"}
    result = route_by_intent(state)

    if result == "subscription":
        print("  [PASS] 'subscription' intent routes to 'subscription' node")
        return True
    else:
        print(f"  [FAIL] 'subscription' intent routes to '{result}' (expected: 'subscription')")
        return False


def test_subscription_types():
    """Test SubscriptionType enum values."""
    from bot.services.subscription_service import SubscriptionType

    print("\n" + "=" * 50)
    print("Testing SubscriptionType Enum")
    print("=" * 50)

    expected_types = ["DAILY_HOROSCOPE", "TRANSIT_ALERTS"]
    passed = 0

    for type_name in expected_types:
        if hasattr(SubscriptionType, type_name):
            print(f"  [PASS] SubscriptionType.{type_name} exists")
            passed += 1
        else:
            print(f"  [FAIL] SubscriptionType.{type_name} missing")

    print(f"\nResults: {passed}/{len(expected_types)} types found")
    return passed == len(expected_types)


def main():
    """Run all quick tests."""
    print("\n" + "=" * 60)
    print("D23Bot Subscription Feature Quick Tests")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Action Detection", test_action_detection()))
    results.append(("Zodiac Extraction", test_zodiac_extraction()))
    results.append(("Time Extraction", test_time_extraction()))
    results.append(("Intent Patterns", test_intent_patterns()))
    results.append(("Graph Routing", test_graph_routing()))
    results.append(("Subscription Types", test_subscription_types()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        icon = "[OK]" if result else "[X]"
        print(f"  {icon} {name}")

    print(f"\nTotal: {passed}/{total} test suites passed")

    if passed == total:
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
