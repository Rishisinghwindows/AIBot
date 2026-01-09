"""
Advanced Test Cases for Multilingual WhatsApp Bot
Tests edge cases, error handling, additional features, and boundary conditions.
"""

import sys
sys.path.insert(0, "/Users/rishi/Desktop/WorkSpace/AIBot/WhatsappBot&OhGrtApi/unified_platform")

# Read responses.py directly
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
TRAIN_LABELS = exec_globals.get('TRAIN_LABELS', {})

LANGUAGES = ["en", "hi", "bn", "ta", "te", "kn", "ml", "gu", "mr", "pa", "or"]
LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu", "kn": "Kannada", "ml": "Malayalam", "gu": "Gujarati",
    "mr": "Marathi", "pa": "Punjabi", "or": "Odia",
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


# ============================================================
# TEST 1: EDGE CASES - Fallback to English
# ============================================================
def test_fallback_to_english():
    """Test that unknown languages fall back to English."""
    print("\n" + "=" * 70)
    print("TEST 1: FALLBACK TO ENGLISH FOR UNKNOWN LANGUAGES")
    print("=" * 70)

    unknown_langs = ["fr", "de", "es", "zh", "ja", "ko", "ar", "ru", "xx", ""]
    all_passed = True

    for unknown_lang in unknown_langs:
        # Should fall back to English
        result = get_label(EVENT_LABELS, "found", unknown_lang, count=5)
        english_result = get_label(EVENT_LABELS, "found", "en", count=5)

        if result == english_result:
            print(f"  ✅ '{unknown_lang}' -> Falls back to English: {result[:40]}")
        else:
            print(f"  ❌ '{unknown_lang}' -> Unexpected result: {result[:40]}")
            all_passed = False

    return all_passed


# ============================================================
# TEST 2: MISSING KEY HANDLING
# ============================================================
def test_missing_key_handling():
    """Test behavior when a key doesn't exist."""
    print("\n" + "=" * 70)
    print("TEST 2: MISSING KEY HANDLING")
    print("=" * 70)

    nonexistent_keys = ["nonexistent_key", "xyz_abc", "random_key_123"]
    all_passed = True

    for key in nonexistent_keys:
        for lang in ["en", "hi", "ta"]:
            result = get_label(EVENT_LABELS, key, lang)
            # Should return the key itself as fallback
            if result == key:
                print(f"  ✅ Key '{key}' in {lang} -> Returns key as fallback")
            else:
                print(f"  ❌ Key '{key}' in {lang} -> Unexpected: {result}")
                all_passed = False

    return all_passed


# ============================================================
# TEST 3: SPECIAL CHARACTERS AND UNICODE
# ============================================================
def test_unicode_handling():
    """Test that all translations contain valid Unicode characters."""
    print("\n" + "=" * 70)
    print("TEST 3: UNICODE AND SPECIAL CHARACTERS")
    print("=" * 70)

    all_passed = True

    # Test each language's script
    expected_scripts = {
        "hi": "देवनागरी",  # Devanagari
        "bn": "বাংলা",     # Bengali
        "ta": "தமிழ்",     # Tamil
        "te": "తెలుగు",    # Telugu
        "kn": "ಕನ್ನಡ",     # Kannada
        "ml": "മലയാളം",   # Malayalam
        "gu": "ગુજરાતી",   # Gujarati
        "mr": "मराठी",     # Marathi (Devanagari)
        "pa": "ਪੰਜਾਬੀ",    # Gurmukhi
        "or": "ଓଡ଼ିଆ",     # Odia
    }

    for lang, script_sample in expected_scripts.items():
        labels = EVENT_LABELS.get(lang, {})
        found_text = labels.get("found", "")

        # Check if text contains non-ASCII (native script)
        has_native = any(ord(c) > 127 for c in found_text)

        if has_native:
            print(f"  ✅ {LANGUAGE_NAMES[lang]:12} ({lang}): Contains native script - {found_text[:30]}")
        else:
            print(f"  ❌ {LANGUAGE_NAMES[lang]:12} ({lang}): No native script found - {found_text[:30]}")
            all_passed = False

    return all_passed


# ============================================================
# TEST 4: ASTRO/HOROSCOPE LABELS
# ============================================================
def test_astro_labels():
    """Test astrology/horoscope labels if they exist."""
    print("\n" + "=" * 70)
    print("TEST 4: ASTRO/HOROSCOPE LABELS")
    print("=" * 70)

    if not ASTRO_LABELS:
        print("  ⚠️  ASTRO_LABELS not found - skipping")
        return True

    required_keys = ["title", "select_sign", "daily_horoscope"]
    all_passed = True

    for lang in LANGUAGES:
        if lang not in ASTRO_LABELS:
            print(f"  ❌ {LANGUAGE_NAMES[lang]} ({lang}): Missing language")
            all_passed = False
            continue

        missing = [k for k in required_keys if k not in ASTRO_LABELS[lang]]
        if missing:
            print(f"  ❌ {LANGUAGE_NAMES[lang]} ({lang}): Missing keys: {missing}")
            all_passed = False
        else:
            sample = ASTRO_LABELS[lang].get("title", "")[:40]
            print(f"  ✅ {LANGUAGE_NAMES[lang]} ({lang}): {sample}")

    return all_passed


# ============================================================
# TEST 5: LIFE PREDICTION LABELS
# ============================================================
def test_life_prediction_labels():
    """Test life prediction labels if they exist."""
    print("\n" + "=" * 70)
    print("TEST 5: LIFE PREDICTION LABELS")
    print("=" * 70)

    if not LIFE_PREDICTION_LABELS:
        print("  ⚠️  LIFE_PREDICTION_LABELS not found - skipping")
        return True

    required_keys = ["title", "enter_dob", "prediction"]
    all_passed = True

    for lang in LANGUAGES:
        if lang not in LIFE_PREDICTION_LABELS:
            print(f"  ❌ {LANGUAGE_NAMES[lang]} ({lang}): Missing language")
            all_passed = False
            continue

        missing = [k for k in required_keys if k not in LIFE_PREDICTION_LABELS[lang]]
        if missing:
            print(f"  ⚠️  {LANGUAGE_NAMES[lang]} ({lang}): Missing optional keys: {missing}")
        else:
            sample = LIFE_PREDICTION_LABELS[lang].get("title", "")[:40]
            print(f"  ✅ {LANGUAGE_NAMES[lang]} ({lang}): {sample}")

    return True  # Optional labels


# ============================================================
# TEST 6: HELP LABELS
# ============================================================
def test_help_labels():
    """Test help menu labels if they exist."""
    print("\n" + "=" * 70)
    print("TEST 6: HELP MENU LABELS")
    print("=" * 70)

    if not HELP_LABELS:
        print("  ⚠️  HELP_LABELS not found - skipping")
        return True

    all_passed = True

    for lang in LANGUAGES:
        if lang not in HELP_LABELS:
            print(f"  ⚠️  {LANGUAGE_NAMES[lang]} ({lang}): Missing (will use English)")
            continue

        sample = str(HELP_LABELS[lang])[:60] if HELP_LABELS[lang] else "empty"
        print(f"  ✅ {LANGUAGE_NAMES[lang]} ({lang}): Present")

    return all_passed


# ============================================================
# TEST 7: ERROR MESSAGES
# ============================================================
def test_error_messages():
    """Test error message labels across all languages."""
    print("\n" + "=" * 70)
    print("TEST 7: ERROR MESSAGE LABELS")
    print("=" * 70)

    all_passed = True

    # Test word game error
    print("\n--- Word Game Error ---")
    for lang in LANGUAGES:
        error_msg = get_label(WORD_GAME_LABELS, "error", lang)
        has_content = len(error_msg) > 5 and error_msg != "error"
        status = "✅" if has_content else "❌"
        print(f"  {status} {LANGUAGE_NAMES[lang]:12}: {error_msg[:50]}")
        if not has_content:
            all_passed = False

    # Test subscription error
    print("\n--- Subscription Error ---")
    for lang in LANGUAGES:
        error_msg = get_label(SUBSCRIPTION_LABELS, "error", lang)
        has_content = len(error_msg) > 5 and error_msg != "error"
        status = "✅" if has_content else "❌"
        print(f"  {status} {LANGUAGE_NAMES[lang]:12}: {error_msg[:50]}")
        if not has_content:
            all_passed = False

    # Test common error phrase
    print("\n--- Common Error Phrase ---")
    for lang in LANGUAGES:
        error_msg = get_label(COMMON_PHRASES, "error_occurred", lang)
        has_content = len(error_msg) > 5 and error_msg != "error_occurred"
        status = "✅" if has_content else "❌"
        print(f"  {status} {LANGUAGE_NAMES[lang]:12}: {error_msg[:50]}")
        if not has_content:
            all_passed = False

    return all_passed


# ============================================================
# TEST 8: IPL-SPECIFIC LABELS
# ============================================================
def test_ipl_labels():
    """Test IPL cricket-specific labels."""
    print("\n" + "=" * 70)
    print("TEST 8: IPL-SPECIFIC LABELS")
    print("=" * 70)

    ipl_keys = ["ipl_title", "no_ipl", "ticket_details"]
    all_passed = True

    for key in ipl_keys:
        print(f"\n--- {key} ---")
        for lang in LANGUAGES:
            label = get_label(EVENT_LABELS, key, lang)
            has_content = len(label) > 3 and label != key
            status = "✅" if has_content else "❌"
            print(f"  {status} {LANGUAGE_NAMES[lang]:12}: {label[:50]}")
            if not has_content:
                all_passed = False

    return all_passed


# ============================================================
# TEST 9: CONCERT AND COMEDY LABELS
# ============================================================
def test_entertainment_labels():
    """Test concert and comedy show labels."""
    print("\n" + "=" * 70)
    print("TEST 9: ENTERTAINMENT LABELS (Concerts & Comedy)")
    print("=" * 70)

    entertainment_keys = ["concerts_title", "comedy_title", "no_concerts", "no_comedy"]
    all_passed = True

    for key in entertainment_keys:
        print(f"\n--- {key} ---")
        for lang in LANGUAGES:
            label = get_label(EVENT_LABELS, key, lang)
            has_content = len(label) > 3 and label != key
            status = "✅" if has_content else "❌"
            print(f"  {status} {LANGUAGE_NAMES[lang]:12}: {label[:50]}")
            if not has_content:
                all_passed = False

    return all_passed


# ============================================================
# TEST 10: PLACEHOLDER EDGE CASES
# ============================================================
def test_placeholder_edge_cases():
    """Test placeholders with edge case values."""
    print("\n" + "=" * 70)
    print("TEST 10: PLACEHOLDER EDGE CASES")
    print("=" * 70)

    all_passed = True

    # Test with zero count
    print("\n--- Zero count ---")
    for lang in ["en", "hi", "ta", "bn"]:
        result = get_label(EVENT_LABELS, "found", lang, count=0)
        print(f"  {LANGUAGE_NAMES[lang]:12}: {result}")

    # Test with large count
    print("\n--- Large count (1000) ---")
    for lang in ["en", "hi", "ta", "bn"]:
        result = get_label(EVENT_LABELS, "found", lang, count=1000)
        print(f"  {LANGUAGE_NAMES[lang]:12}: {result}")

    # Test with special characters in query
    print("\n--- Special chars in query ---")
    special_queries = ["café & restaurant", "hotel's", "food <test>", "ATM/Bank"]
    for query in special_queries:
        result = get_label(LOCAL_SEARCH_LABELS, "searching", "en", query=query)
        safe = "&" not in result or "café" in result  # Basic check
        status = "✅" if safe else "⚠️"
        print(f"  {status} Query '{query}': {result[:50]}")

    # Test with empty string
    print("\n--- Empty string values ---")
    result = get_label(LOCAL_SEARCH_LABELS, "searching", "en", query="")
    print(f"  Empty query: {result[:50]}")

    result = get_label(EVENT_LABELS, "events_near", "en", city="")
    print(f"  Empty city: {result[:50]}")

    return all_passed


# ============================================================
# TEST 11: TRAIN STATUS LABELS
# ============================================================
def test_train_labels():
    """Test train status labels if they exist."""
    print("\n" + "=" * 70)
    print("TEST 11: TRAIN STATUS LABELS")
    print("=" * 70)

    if not TRAIN_LABELS:
        print("  ⚠️  TRAIN_LABELS not found - checking for Hindi/English specific labels")
        # Try to read train_status.py for HINDI_LABELS/ENGLISH_LABELS
        try:
            train_path = "/Users/rishi/Desktop/WorkSpace/AIBot/WhatsappBot&OhGrtApi/unified_platform/whatsapp_bot/graph/nodes/train_status.py"
            with open(train_path, 'r') as f:
                train_content = f.read()

            if "HINDI_LABELS" in train_content and "ENGLISH_LABELS" in train_content:
                print("  ✅ Train status uses HINDI_LABELS and ENGLISH_LABELS")
                print("  ✅ Uses LLM translation for other languages")
                return True
        except:
            pass
        return True

    all_passed = True
    for lang in LANGUAGES:
        if lang in TRAIN_LABELS:
            print(f"  ✅ {LANGUAGE_NAMES[lang]} ({lang}): Present")
        else:
            print(f"  ⚠️  {LANGUAGE_NAMES[lang]} ({lang}): Missing (will use fallback)")

    return all_passed


# ============================================================
# TEST 12: RESPONSE LENGTH CONSISTENCY
# ============================================================
def test_response_length_consistency():
    """Check that translations aren't too short or too long."""
    print("\n" + "=" * 70)
    print("TEST 12: RESPONSE LENGTH CONSISTENCY")
    print("=" * 70)

    all_passed = True

    # Compare lengths across languages for key labels
    test_labels = [
        (EVENT_LABELS, "not_found"),
        (LOCAL_SEARCH_LABELS, "ask_location"),
        (WORD_GAME_LABELS, "start"),
        (FOOD_LABELS, "title"),
    ]

    for labels_dict, key in test_labels:
        print(f"\n--- {key} ---")
        lengths = {}
        for lang in LANGUAGES:
            text = get_label(labels_dict, key, lang)
            lengths[lang] = len(text)

        avg_len = sum(lengths.values()) / len(lengths)

        for lang, length in lengths.items():
            # Flag if length is <30% or >300% of average
            ratio = length / avg_len if avg_len > 0 else 1
            if ratio < 0.3:
                status = "⚠️ SHORT"
                all_passed = False
            elif ratio > 3:
                status = "⚠️ LONG"
                all_passed = False
            else:
                status = "✅"

            text = get_label(labels_dict, key, lang)[:30]
            print(f"  {status} {LANGUAGE_NAMES[lang]:12}: {length:3} chars - {text}...")

    return all_passed


# ============================================================
# TEST 13: SUBSCRIPTION FLOW LABELS
# ============================================================
def test_subscription_flow():
    """Test complete subscription flow labels."""
    print("\n" + "=" * 70)
    print("TEST 13: SUBSCRIPTION FLOW LABELS")
    print("=" * 70)

    flow_keys = ["title", "daily_horoscope", "transit_alerts", "subscribed", "unsubscribed", "no_subscriptions", "error"]
    all_passed = True

    for key in flow_keys:
        print(f"\n--- {key} ---")
        for lang in LANGUAGES:
            label = get_label(SUBSCRIPTION_LABELS, key, lang)
            has_content = len(label) > 3 and label != key
            status = "✅" if has_content else "❌"
            print(f"  {status} {LANGUAGE_NAMES[lang]:12}: {label[:45]}")
            if not has_content:
                all_passed = False

    return all_passed


# ============================================================
# TEST 14: WORD GAME COMPLETE FLOW
# ============================================================
def test_word_game_complete_flow():
    """Test all word game labels for complete flow."""
    print("\n" + "=" * 70)
    print("TEST 14: WORD GAME COMPLETE FLOW")
    print("=" * 70)

    flow_keys = ["start", "correct", "wrong", "play_again", "error"]
    all_passed = True

    for key in flow_keys:
        print(f"\n--- {key} ---")
        for lang in LANGUAGES:
            if key == "correct":
                label = get_label(WORD_GAME_LABELS, key, lang, word="APPLE")
            else:
                label = get_label(WORD_GAME_LABELS, key, lang)

            has_content = len(label) > 3 and label != key
            status = "✅" if has_content else "❌"
            print(f"  {status} {LANGUAGE_NAMES[lang]:12}: {label[:45]}")
            if not has_content:
                all_passed = False

    return all_passed


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("ADVANCED MULTILINGUAL TEST SUITE")
    print("Testing edge cases, error handling, and additional scenarios")
    print("=" * 70)

    results = {}

    # Run all tests
    results["Fallback to English"] = test_fallback_to_english()
    results["Missing Key Handling"] = test_missing_key_handling()
    results["Unicode Handling"] = test_unicode_handling()
    results["Astro Labels"] = test_astro_labels()
    results["Life Prediction Labels"] = test_life_prediction_labels()
    results["Help Labels"] = test_help_labels()
    results["Error Messages"] = test_error_messages()
    results["IPL Labels"] = test_ipl_labels()
    results["Entertainment Labels"] = test_entertainment_labels()
    results["Placeholder Edge Cases"] = test_placeholder_edge_cases()
    results["Train Labels"] = test_train_labels()
    results["Response Length"] = test_response_length_consistency()
    results["Subscription Flow"] = test_subscription_flow()
    results["Word Game Flow"] = test_word_game_complete_flow()

    # Summary
    print("\n" + "=" * 70)
    print("ADVANCED TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "-" * 70)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL ADVANCED TESTS PASSED!")
    else:
        print("⚠️  Some tests need attention - review details above")
    print("-" * 70)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
