"""
Test script for verifying multilingual support across all WhatsApp bot nodes.
Tests each node with different language codes and verifies localized responses.
"""

import asyncio
import sys
from typing import Dict, List, Tuple

# Add the project to path
sys.path.insert(0, "/Users/rishi/Desktop/WorkSpace/AIBot/WhatsappBot&OhGrtApi/unified_platform")

# Import i18n label functions
from common.i18n.responses import (
    get_word_game_label,
    get_event_label,
    get_local_search_label,
    get_food_label,
    get_subscription_label,
    get_phrase,
)

# Languages to test
LANGUAGES = ["en", "hi", "bn", "ta", "te", "kn", "ml", "gu", "mr", "pa", "or"]

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "gu": "Gujarati",
    "mr": "Marathi",
    "pa": "Punjabi",
    "or": "Odia",
}


def test_word_game_labels():
    """Test word game labels for all languages."""
    print("\n" + "="*60)
    print("TESTING: Word Game Labels")
    print("="*60)

    keys_to_test = ["start", "correct", "play_again", "wrong", "error"]
    results = []

    for lang in LANGUAGES:
        lang_results = []
        for key in keys_to_test:
            label = get_word_game_label(key, lang)
            # Check if it's not returning the key itself (fallback)
            is_translated = label != key and len(label) > 0
            lang_results.append((key, is_translated, label[:50] if len(label) > 50 else label))

        all_passed = all(r[1] for r in lang_results)
        status = "✅ PASS" if all_passed else "❌ FAIL"
        results.append((lang, all_passed))

        print(f"\n{LANGUAGE_NAMES[lang]} ({lang}): {status}")
        for key, passed, sample in lang_results:
            icon = "✓" if passed else "✗"
            print(f"  {icon} {key}: {sample}")

    return results


def test_event_labels():
    """Test event labels for all languages."""
    print("\n" + "="*60)
    print("TESTING: Event Labels")
    print("="*60)

    keys_to_test = [
        "title", "ask_location", "not_found", "found", "ipl_title",
        "concerts_title", "comedy_title", "and_more", "ticket_details",
        "no_ipl", "no_concerts", "events_near", "looking_for_events"
    ]
    results = []

    for lang in LANGUAGES:
        lang_results = []
        for key in keys_to_test:
            try:
                # Some keys need kwargs
                if key in ["found", "and_more"]:
                    label = get_event_label(key, lang, count=5)
                elif key == "events_near":
                    label = get_event_label(key, lang, city="Mumbai")
                else:
                    label = get_event_label(key, lang)

                is_translated = label != key and len(label) > 0
                lang_results.append((key, is_translated, label[:40] if len(label) > 40 else label))
            except Exception as e:
                lang_results.append((key, False, f"ERROR: {str(e)[:30]}"))

        all_passed = all(r[1] for r in lang_results)
        status = "✅ PASS" if all_passed else "❌ FAIL"
        results.append((lang, all_passed))

        print(f"\n{LANGUAGE_NAMES[lang]} ({lang}): {status}")
        for key, passed, sample in lang_results:
            icon = "✓" if passed else "✗"
            print(f"  {icon} {key}: {sample}")

    return results


def test_local_search_labels():
    """Test local search labels for all languages."""
    print("\n" + "="*60)
    print("TESTING: Local Search Labels")
    print("="*60)

    keys_to_test = [
        "title", "ask_location", "not_found", "found", "found_places",
        "searching", "no_places_for", "try_again", "local_search",
        "what_search", "away", "reviews"
    ]
    results = []

    for lang in LANGUAGES:
        lang_results = []
        for key in keys_to_test:
            try:
                if key == "found":
                    label = get_local_search_label(key, lang, count=5)
                elif key == "searching":
                    label = get_local_search_label(key, lang, query="hotel")
                elif key == "no_places_for":
                    label = get_local_search_label(key, lang, query="restaurant")
                else:
                    label = get_local_search_label(key, lang)

                is_translated = label != key and len(label) > 0
                lang_results.append((key, is_translated, label[:40] if len(label) > 40 else label))
            except Exception as e:
                lang_results.append((key, False, f"ERROR: {str(e)[:30]}"))

        all_passed = all(r[1] for r in lang_results)
        status = "✅ PASS" if all_passed else "❌ FAIL"
        results.append((lang, all_passed))

        print(f"\n{LANGUAGE_NAMES[lang]} ({lang}): {status}")
        for key, passed, sample in lang_results:
            icon = "✓" if passed else "✗"
            print(f"  {icon} {key}: {sample}")

    return results


def test_food_labels():
    """Test food labels for all languages."""
    print("\n" + "="*60)
    print("TESTING: Food Labels")
    print("="*60)

    keys_to_test = ["title", "ask_location", "not_found", "or_city"]
    results = []

    for lang in LANGUAGES:
        lang_results = []
        for key in keys_to_test:
            try:
                label = get_food_label(key, lang)
                is_translated = label != key and len(label) > 0
                lang_results.append((key, is_translated, label[:40] if len(label) > 40 else label))
            except Exception as e:
                lang_results.append((key, False, f"ERROR: {str(e)[:30]}"))

        all_passed = all(r[1] for r in lang_results)
        status = "✅ PASS" if all_passed else "❌ FAIL"
        results.append((lang, all_passed))

        print(f"\n{LANGUAGE_NAMES[lang]} ({lang}): {status}")
        for key, passed, sample in lang_results:
            icon = "✓" if passed else "✗"
            print(f"  {icon} {key}: {sample}")

    return results


def test_subscription_labels():
    """Test subscription labels for all languages."""
    print("\n" + "="*60)
    print("TESTING: Subscription Labels")
    print("="*60)

    keys_to_test = [
        "title", "daily_horoscope", "transit_alerts", "subscribed",
        "unsubscribed", "no_subscriptions", "error"
    ]
    results = []

    for lang in LANGUAGES:
        lang_results = []
        for key in keys_to_test:
            try:
                label = get_subscription_label(key, lang)
                is_translated = label != key and len(label) > 0
                lang_results.append((key, is_translated, label[:40] if len(label) > 40 else label))
            except Exception as e:
                lang_results.append((key, False, f"ERROR: {str(e)[:30]}"))

        all_passed = all(r[1] for r in lang_results)
        status = "✅ PASS" if all_passed else "❌ FAIL"
        results.append((lang, all_passed))

        print(f"\n{LANGUAGE_NAMES[lang]} ({lang}): {status}")
        for key, passed, sample in lang_results:
            icon = "✓" if passed else "✗"
            print(f"  {icon} {key}: {sample}")

    return results


def test_common_phrases():
    """Test common phrases for all languages."""
    print("\n" + "="*60)
    print("TESTING: Common Phrases")
    print("="*60)

    keys_to_test = ["error_occurred", "try_again", "welcome"]
    results = []

    for lang in LANGUAGES:
        lang_results = []
        for key in keys_to_test:
            try:
                label = get_phrase(key, lang)
                is_translated = label != key and len(label) > 0
                lang_results.append((key, is_translated, label[:40] if len(label) > 40 else label))
            except Exception as e:
                lang_results.append((key, False, f"ERROR: {str(e)[:30]}"))

        all_passed = all(r[1] for r in lang_results)
        status = "✅ PASS" if all_passed else "❌ FAIL"
        results.append((lang, all_passed))

        print(f"\n{LANGUAGE_NAMES[lang]} ({lang}): {status}")
        for key, passed, sample in lang_results:
            icon = "✓" if passed else "✗"
            print(f"  {icon} {key}: {sample}")

    return results


def print_summary(all_results: Dict[str, List[Tuple[str, bool]]]):
    """Print summary of all test results."""
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    total_tests = 0
    total_passed = 0

    for test_name, results in all_results.items():
        passed = sum(1 for _, p in results if p)
        total = len(results)
        total_tests += total
        total_passed += passed

        status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
        print(f"{status} {test_name}: {passed}/{total} languages passed")

    print("\n" + "-"*60)
    overall = "✅ ALL TESTS PASSED" if total_passed == total_tests else f"⚠️ {total_passed}/{total_tests} PASSED"
    print(f"\nOverall: {overall}")

    # Show which languages have issues
    failed_langs = set()
    for test_name, results in all_results.items():
        for lang, passed in results:
            if not passed:
                failed_langs.add(lang)

    if failed_langs:
        print(f"\nLanguages with issues: {', '.join(LANGUAGE_NAMES[l] for l in sorted(failed_langs))}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MULTILINGUAL SUPPORT VERIFICATION TESTS")
    print("Testing 11 Indian languages across all WhatsApp bot nodes")
    print("="*60)

    all_results = {}

    # Run all tests
    all_results["Word Game"] = test_word_game_labels()
    all_results["Events"] = test_event_labels()
    all_results["Local Search"] = test_local_search_labels()
    all_results["Food"] = test_food_labels()
    all_results["Subscription"] = test_subscription_labels()
    all_results["Common Phrases"] = test_common_phrases()

    # Print summary
    print_summary(all_results)


if __name__ == "__main__":
    main()
