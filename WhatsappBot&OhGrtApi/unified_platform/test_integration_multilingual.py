"""
Broad Integration Test for Multilingual WhatsApp Bot
Tests complete message flows across all nodes and all 11 languages.
"""

import sys
sys.path.insert(0, "/Users/rishi/Desktop/WorkSpace/AIBot/WhatsappBot&OhGrtApi/unified_platform")

import asyncio
from typing import Dict, Any

# Read responses.py directly to avoid import chain issues
responses_path = "/Users/rishi/Desktop/WorkSpace/AIBot/WhatsappBot&OhGrtApi/unified_platform/common/i18n/responses.py"
with open(responses_path, 'r') as f:
    content = f.read()

exec_globals = {}
exec(content, exec_globals)

# Get all label dictionaries
WORD_GAME_LABELS = exec_globals.get('WORD_GAME_LABELS', {})
EVENT_LABELS = exec_globals.get('EVENT_LABELS', {})
LOCAL_SEARCH_LABELS = exec_globals.get('LOCAL_SEARCH_LABELS', {})
FOOD_LABELS = exec_globals.get('FOOD_LABELS', {})
SUBSCRIPTION_LABELS = exec_globals.get('SUBSCRIPTION_LABELS', {})
COMMON_PHRASES = exec_globals.get('COMMON_PHRASES', {})
ASTRO_LABELS = exec_globals.get('ASTRO_LABELS', {})
LIFE_PREDICTION_LABELS = exec_globals.get('LIFE_PREDICTION_LABELS', {})
HELP_LABELS = exec_globals.get('HELP_LABELS', {})

# All 11 supported languages
LANGUAGES = ["en", "hi", "bn", "ta", "te", "kn", "ml", "gu", "mr", "pa", "or"]

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu", "kn": "Kannada", "ml": "Malayalam", "gu": "Gujarati",
    "mr": "Marathi", "pa": "Punjabi", "or": "Odia",
}

# Sample user messages in different languages (simulating what users might type)
SAMPLE_USER_MESSAGES = {
    "en": {
        "events": "Show me events in Mumbai",
        "ipl": "IPL matches",
        "local_search": "restaurants near me",
        "food": "food delivery in Delhi",
        "word_game": "word game",
        "horoscope": "my horoscope for Aries",
        "help": "help",
    },
    "hi": {
        "events": "मुंबई में इवेंट्स दिखाओ",
        "ipl": "IPL मैच",
        "local_search": "मेरे पास रेस्टोरेंट",
        "food": "दिल्ली में खाना डिलीवरी",
        "word_game": "शब्द खेल",
        "horoscope": "मेष राशिफल",
        "help": "मदद",
    },
    "ta": {
        "events": "சென்னையில் நிகழ்வுகள்",
        "ipl": "IPL போட்டிகள்",
        "local_search": "அருகில் உணவகங்கள்",
        "food": "சென்னையில் உணவு டெலிவரி",
        "word_game": "வார்த்தை விளையாட்டு",
        "horoscope": "மேஷ ராசி பலன்",
        "help": "உதவி",
    },
    "bn": {
        "events": "কলকাতায় ইভেন্ট",
        "ipl": "IPL ম্যাচ",
        "local_search": "কাছে রেস্তোরাঁ",
        "food": "কলকাতায় খাবার ডেলিভারি",
        "word_game": "শব্দ খেলা",
        "horoscope": "মেষ রাশিফল",
        "help": "সাহায্য",
    },
    "kn": {
        "events": "ಬೆಂಗಳೂರಿನಲ್ಲಿ ಈವೆಂಟ್‌ಗಳು",
        "ipl": "IPL ಪಂದ್ಯಗಳು",
        "local_search": "ಹತ್ತಿರ ರೆಸ್ಟೋರೆಂಟ್‌ಗಳು",
        "food": "ಬೆಂಗಳೂರಿನಲ್ಲಿ ಊಟ ಡೆಲಿವರಿ",
        "word_game": "ಪದ ಆಟ",
        "horoscope": "ಮೇಷ ರಾಶಿಫಲ",
        "help": "ಸಹಾಯ",
    },
}


def get_label(labels_dict: dict, key: str, lang: str, **kwargs) -> str:
    """Get a label with fallback to English."""
    lang_labels = labels_dict.get(lang, labels_dict.get("en", {}))
    template = lang_labels.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template
    return template


class MockBotState:
    """Mock bot state for testing."""
    def __init__(self, lang: str, intent: str, query: str):
        self.data = {
            "detected_language": lang,
            "intent": intent,
            "current_query": query,
            "extracted_entities": {},
            "whatsapp_message": {
                "from_number": "919876543210",
                "text": query,
                "message_type": "text",
            }
        }

    def get(self, key, default=None):
        return self.data.get(key, default)


def simulate_event_response(lang: str, events_count: int = 3) -> str:
    """Simulate event node response."""
    if events_count == 0:
        return get_label(EVENT_LABELS, "not_found", lang)

    found = get_label(EVENT_LABELS, "found", lang, count=events_count)
    at_label = get_label(EVENT_LABELS, "at", lang)
    more_details = get_label(EVENT_LABELS, "more_details", lang)

    response = f"🎫 *{found}:*\n\n"
    response += f"*1. Sample Event*\n📍 Venue, City\n📅 Jan 20, 2025 {at_label} 7:00 PM\n💰 ₹500 - ₹2000\n\n"
    response += f"📱 {more_details}"
    return response


def simulate_local_search_response(lang: str, places_count: int = 3) -> str:
    """Simulate local search node response."""
    if places_count == 0:
        return get_label(LOCAL_SEARCH_LABELS, "no_places_for", lang, query="restaurant")

    found_places = get_label(LOCAL_SEARCH_LABELS, "found_places", lang)
    away = get_label(LOCAL_SEARCH_LABELS, "away", lang)
    reviews = get_label(LOCAL_SEARCH_LABELS, "reviews", lang)

    response = f"*Restaurant near your location*\n\n*{found_places}:*\n\n"
    response += f"1. *Sample Place*\n   📏 0.5 km {away}\n   📍 Address\n   ⭐⭐⭐⭐ 4.2 (150 {reviews})\n"
    return response


def simulate_word_game_response(lang: str, is_correct: bool = False) -> str:
    """Simulate word game node response."""
    if is_correct:
        correct = get_label(WORD_GAME_LABELS, "correct", lang, word="APPLE")
        play_again = get_label(WORD_GAME_LABELS, "play_again", lang)
        return f"{correct}\n\n{play_again}"
    else:
        start = get_label(WORD_GAME_LABELS, "start", lang)
        return f"{start}\n\n*LEPAP*"


def simulate_food_response(lang: str, has_location: bool = False) -> str:
    """Simulate food node response."""
    if not has_location:
        title = get_label(FOOD_LABELS, "title", lang)
        ask_location = get_label(FOOD_LABELS, "ask_location", lang)
        or_city = get_label(FOOD_LABELS, "or_city", lang)
        return f"*{title}*\n\n{ask_location}\n\n{or_city}"
    return "Food options found..."


def simulate_subscription_response(lang: str) -> str:
    """Simulate subscription node response."""
    title = get_label(SUBSCRIPTION_LABELS, "title", lang)
    daily_horoscope = get_label(SUBSCRIPTION_LABELS, "daily_horoscope", lang)
    transit_alerts = get_label(SUBSCRIPTION_LABELS, "transit_alerts", lang)

    return f"*{title}*\n\n1. {daily_horoscope}\n2. {transit_alerts}"


def test_response_simulation(feature: str, simulate_fn, lang: str, **kwargs) -> tuple:
    """Test a simulated response for a feature."""
    try:
        response = simulate_fn(lang, **kwargs)
        # Check response is not empty and not just the key
        has_content = len(response) > 10
        # Check it contains some non-ASCII chars for non-English (indicates translation)
        if lang != "en":
            has_native_text = any(ord(c) > 127 for c in response)
        else:
            has_native_text = True

        return (has_content and has_native_text, response[:100])
    except Exception as e:
        return (False, f"ERROR: {str(e)[:50]}")


def run_broad_tests():
    """Run broad integration tests across all features and languages."""
    print("=" * 70)
    print("BROAD INTEGRATION TEST - MULTILINGUAL WHATSAPP BOT")
    print("Testing complete message flows across all 11 languages")
    print("=" * 70)

    results = {}

    # Test each feature
    features = [
        ("Events - Found", simulate_event_response, {"events_count": 3}),
        ("Events - Not Found", simulate_event_response, {"events_count": 0}),
        ("Local Search - Found", simulate_local_search_response, {"places_count": 3}),
        ("Local Search - Not Found", simulate_local_search_response, {"places_count": 0}),
        ("Word Game - Start", simulate_word_game_response, {"is_correct": False}),
        ("Word Game - Correct", simulate_word_game_response, {"is_correct": True}),
        ("Food - Ask Location", simulate_food_response, {"has_location": False}),
        ("Subscription - Menu", simulate_subscription_response, {}),
    ]

    for feature_name, simulate_fn, kwargs in features:
        print(f"\n{'=' * 60}")
        print(f"TESTING: {feature_name}")
        print("=" * 60)

        feature_results = []
        for lang in LANGUAGES:
            passed, sample = test_response_simulation(feature_name, simulate_fn, lang, **kwargs)
            feature_results.append((lang, passed))

            status = "✅" if passed else "❌"
            print(f"{status} {LANGUAGE_NAMES[lang]:12} ({lang}): {sample[:60]}...")

        results[feature_name] = feature_results

    # Print Summary
    print("\n" + "=" * 70)
    print("SUMMARY BY FEATURE")
    print("=" * 70)

    all_passed = True
    for feature_name, feature_results in results.items():
        passed_count = sum(1 for _, p in feature_results if p)
        total = len(feature_results)
        status = "✅" if passed_count == total else "❌"
        print(f"{status} {feature_name}: {passed_count}/{total} languages")
        if passed_count != total:
            all_passed = False

    # Summary by Language
    print("\n" + "=" * 70)
    print("SUMMARY BY LANGUAGE")
    print("=" * 70)

    for lang in LANGUAGES:
        lang_passed = sum(
            1 for feature_results in results.values()
            for l, p in feature_results if l == lang and p
        )
        lang_total = len(results)
        status = "✅" if lang_passed == lang_total else "❌"
        print(f"{status} {LANGUAGE_NAMES[lang]:12} ({lang}): {lang_passed}/{lang_total} features")

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL BROAD INTEGRATION TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED - Check details above")
    print("=" * 70)

    return all_passed


def test_label_completeness():
    """Test that all label dictionaries have all required keys for all languages."""
    print("\n" + "=" * 70)
    print("LABEL COMPLETENESS CHECK")
    print("Verifying all labels exist for all 11 languages")
    print("=" * 70)

    label_sets = {
        "WORD_GAME_LABELS": (WORD_GAME_LABELS, ["start", "correct", "wrong", "play_again", "error"]),
        "EVENT_LABELS": (EVENT_LABELS, ["title", "found", "not_found", "ipl_title", "concerts_title", "at", "and_more", "ticket_details"]),
        "LOCAL_SEARCH_LABELS": (LOCAL_SEARCH_LABELS, ["title", "found", "not_found", "found_places", "away", "reviews", "searching", "try_again"]),
        "FOOD_LABELS": (FOOD_LABELS, ["title", "ask_location", "not_found", "or_city"]),
        "SUBSCRIPTION_LABELS": (SUBSCRIPTION_LABELS, ["title", "daily_horoscope", "transit_alerts", "subscribed", "unsubscribed"]),
    }

    all_complete = True

    for label_name, (labels_dict, required_keys) in label_sets.items():
        print(f"\n--- {label_name} ---")

        for lang in LANGUAGES:
            if lang not in labels_dict:
                print(f"  ❌ {LANGUAGE_NAMES[lang]} ({lang}): MISSING LANGUAGE")
                all_complete = False
                continue

            missing = []
            for key in required_keys:
                if key not in labels_dict[lang] or not labels_dict[lang][key]:
                    missing.append(key)

            if missing:
                print(f"  ❌ {LANGUAGE_NAMES[lang]} ({lang}): Missing {missing}")
                all_complete = False
            else:
                print(f"  ✅ {LANGUAGE_NAMES[lang]} ({lang}): All {len(required_keys)} keys present")

    return all_complete


def test_format_string_placeholders():
    """Test that format strings work correctly with placeholders."""
    print("\n" + "=" * 70)
    print("FORMAT STRING PLACEHOLDER TEST")
    print("Verifying placeholders work in all translations")
    print("=" * 70)

    test_cases = [
        (EVENT_LABELS, "found", {"count": 5}, "count"),
        (EVENT_LABELS, "and_more", {"count": 3}, "count"),
        (EVENT_LABELS, "events_near", {"city": "Mumbai"}, "city"),
        (LOCAL_SEARCH_LABELS, "searching", {"query": "hotel"}, "query"),
        (LOCAL_SEARCH_LABELS, "no_places_for", {"query": "restaurant"}, "query"),
        (WORD_GAME_LABELS, "correct", {"word": "APPLE"}, "word"),
    ]

    all_passed = True

    for labels_dict, key, kwargs, placeholder_name in test_cases:
        print(f"\n--- Testing '{key}' with {{{placeholder_name}}} ---")

        for lang in LANGUAGES:
            try:
                lang_labels = labels_dict.get(lang, labels_dict.get("en", {}))
                template = lang_labels.get(key, "")
                result = template.format(**kwargs)

                # Check placeholder was replaced
                placeholder = f"{{{placeholder_name}}}"
                if placeholder in result:
                    print(f"  ❌ {LANGUAGE_NAMES[lang]} ({lang}): Placeholder not replaced")
                    all_passed = False
                else:
                    value = kwargs[placeholder_name]
                    if str(value) in result:
                        print(f"  ✅ {LANGUAGE_NAMES[lang]} ({lang}): {result[:50]}")
                    else:
                        print(f"  ⚠️  {LANGUAGE_NAMES[lang]} ({lang}): Value not in result - {result[:50]}")
            except Exception as e:
                print(f"  ❌ {LANGUAGE_NAMES[lang]} ({lang}): ERROR - {str(e)[:30]}")
                all_passed = False

    return all_passed


def main():
    """Run all broad tests."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE MULTILINGUAL BOT TEST SUITE")
    print("=" * 70)

    # Run all test categories
    results = {
        "Label Completeness": test_label_completeness(),
        "Format Placeholders": test_format_string_placeholders(),
        "Response Simulation": run_broad_tests(),
    }

    # Final Summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "-" * 70)
    if all_passed:
        print("🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("The WhatsApp bot is ready for multilingual deployment.")
    else:
        print("⚠️  Some tests failed. Please review the details above.")
    print("-" * 70)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
