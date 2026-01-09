"""
Simple test script for verifying multilingual support.
Directly imports the responses module without dependencies.
"""

import sys
sys.path.insert(0, "/Users/rishi/Desktop/WorkSpace/AIBot/WhatsappBot&OhGrtApi/unified_platform")

# Read and exec the labels directly from responses.py
import re

responses_path = "/Users/rishi/Desktop/WorkSpace/AIBot/WhatsappBot&OhGrtApi/unified_platform/common/i18n/responses.py"
with open(responses_path, 'r') as f:
    content = f.read()

# Execute to get the dictionaries
exec_globals = {}
exec(content, exec_globals)

# Get all label dictionaries
WORD_GAME_LABELS = exec_globals.get('WORD_GAME_LABELS', {})
EVENT_LABELS = exec_globals.get('EVENT_LABELS', {})
LOCAL_SEARCH_LABELS = exec_globals.get('LOCAL_SEARCH_LABELS', {})
FOOD_LABELS = exec_globals.get('FOOD_LABELS', {})
SUBSCRIPTION_LABELS = exec_globals.get('SUBSCRIPTION_LABELS', {})
COMMON_PHRASES = exec_globals.get('COMMON_PHRASES', {})

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


def test_labels(name: str, labels_dict: dict, required_keys: list):
    """Test a label dictionary for all languages."""
    print(f"\n{'='*60}")
    print(f"TESTING: {name}")
    print(f"{'='*60}")

    all_passed = True

    for lang in LANGUAGES:
        if lang not in labels_dict:
            print(f"\n{LANGUAGE_NAMES[lang]} ({lang}): ❌ MISSING LANGUAGE")
            all_passed = False
            continue

        lang_labels = labels_dict[lang]
        missing_keys = []
        found_keys = []

        for key in required_keys:
            if key in lang_labels and lang_labels[key]:
                found_keys.append(key)
            else:
                missing_keys.append(key)

        if missing_keys:
            print(f"\n{LANGUAGE_NAMES[lang]} ({lang}): ❌ FAIL")
            print(f"  Missing keys: {missing_keys}")
            all_passed = False
        else:
            print(f"\n{LANGUAGE_NAMES[lang]} ({lang}): ✅ PASS ({len(found_keys)} keys)")
            # Show a sample translation
            sample_key = required_keys[0]
            sample_val = lang_labels.get(sample_key, "")[:50]
            print(f"  Sample ({sample_key}): {sample_val}")

    return all_passed


def main():
    print("\n" + "="*60)
    print("MULTILINGUAL SUPPORT VERIFICATION TESTS")
    print("Testing 11 Indian languages across all WhatsApp bot nodes")
    print("="*60)

    results = {}

    # Test Word Game Labels
    word_game_keys = ["start", "correct", "play_again", "wrong", "error"]
    results["Word Game"] = test_labels("Word Game Labels", WORD_GAME_LABELS, word_game_keys)

    # Test Event Labels
    event_keys = [
        "title", "ask_location", "not_found", "found", "ipl_title",
        "concerts_title", "comedy_title", "and_more", "ticket_details",
        "no_ipl", "no_concerts", "no_comedy", "events_near", "no_events_near",
        "looking_for_events", "tell_me", "search_by_city", "football_matches"
    ]
    results["Events"] = test_labels("Event Labels", EVENT_LABELS, event_keys)

    # Test Local Search Labels
    local_search_keys = [
        "title", "ask_location", "not_found", "found", "found_places",
        "searching", "no_places_for", "no_within_radius", "try_again",
        "local_search", "what_search", "example", "away", "reviews"
    ]
    results["Local Search"] = test_labels("Local Search Labels", LOCAL_SEARCH_LABELS, local_search_keys)

    # Test Food Labels
    food_keys = ["title", "ask_location", "not_found", "or_city"]
    results["Food"] = test_labels("Food Labels", FOOD_LABELS, food_keys)

    # Test Subscription Labels
    subscription_keys = [
        "title", "daily_horoscope", "transit_alerts", "subscribed",
        "unsubscribed", "no_subscriptions", "error"
    ]
    results["Subscription"] = test_labels("Subscription Labels", SUBSCRIPTION_LABELS, subscription_keys)

    # Test Common Phrases
    common_keys = ["error_occurred", "try_again"]
    results["Common Phrases"] = test_labels("Common Phrases", COMMON_PHRASES, common_keys)

    # Print Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "-"*60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED - Please check the details above")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
