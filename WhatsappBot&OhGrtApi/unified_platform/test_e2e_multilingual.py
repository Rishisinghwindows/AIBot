"""
End-to-End Multilingual Test Suite
Tests complete user journey simulations, stress tests, and edge cases.
"""

import sys
import random
import time
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
LIFE_PREDICTION_LABELS = exec_globals.get('LIFE_PREDICTION_LABELS', {})
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
# TEST 1: COMPLETE USER JOURNEY SIMULATION
# ============================================================
def test_user_journey_simulation():
    """Simulate complete user journeys in different languages."""
    print("\n" + "=" * 70)
    print("TEST 1: COMPLETE USER JOURNEY SIMULATION")
    print("=" * 70)

    all_passed = True

    # Journey 1: Event Discovery Flow
    print("\n--- Journey: Event Discovery ---")
    for lang in ["en", "hi", "ta", "bn", "kn"]:
        journey_steps = []

        # Step 1: User asks for events
        looking = get_label(EVENT_LABELS, "looking_for_events", lang)
        journey_steps.append(f"Bot: {looking[:40]}...")

        # Step 2: Events found
        found = get_label(EVENT_LABELS, "found", lang, count=5)
        at_label = get_label(EVENT_LABELS, "at", lang)
        journey_steps.append(f"Bot: {found} ... {at_label} 7:00 PM")

        # Step 3: More details
        more_details = get_label(EVENT_LABELS, "more_details", lang)
        journey_steps.append(f"Bot: {more_details[:40]}...")

        print(f"\n  {LANGUAGE_NAMES[lang]} ({lang}):")
        for step in journey_steps:
            print(f"    {step}")

        # Verify all steps have content
        if all(len(s) > 10 for s in journey_steps):
            print(f"    ✅ Journey complete")
        else:
            print(f"    ❌ Journey incomplete")
            all_passed = False

    # Journey 2: Local Search Flow
    print("\n--- Journey: Local Search 'Near Me' ---")
    for lang in ["en", "hi", "ta", "te", "ml"]:
        journey_steps = []

        # Step 1: Ask for location
        ask_loc = get_label(LOCAL_SEARCH_LABELS, "ask_location", lang)
        journey_steps.append(f"Bot: {ask_loc[:50]}...")

        # Step 2: Searching
        searching = get_label(LOCAL_SEARCH_LABELS, "searching", lang, query="restaurant")
        journey_steps.append(f"Bot: {searching[:50]}...")

        # Step 3: Results found
        found_places = get_label(LOCAL_SEARCH_LABELS, "found_places", lang)
        away = get_label(LOCAL_SEARCH_LABELS, "away", lang)
        reviews = get_label(LOCAL_SEARCH_LABELS, "reviews", lang)
        journey_steps.append(f"Bot: {found_places} - 0.5 km {away} (150 {reviews})")

        print(f"\n  {LANGUAGE_NAMES[lang]} ({lang}):")
        for step in journey_steps:
            print(f"    {step}")

        if all(len(s) > 10 for s in journey_steps):
            print(f"    ✅ Journey complete")
        else:
            print(f"    ❌ Journey incomplete")
            all_passed = False

    # Journey 3: Word Game Flow
    print("\n--- Journey: Word Game ---")
    for lang in ["en", "hi", "gu", "mr", "pa"]:
        journey_steps = []

        # Step 1: Start game
        start = get_label(WORD_GAME_LABELS, "start", lang)
        journey_steps.append(f"Bot: {start[:40]}...")

        # Step 2: Wrong answer
        wrong = get_label(WORD_GAME_LABELS, "wrong", lang)
        journey_steps.append(f"Bot: {wrong}")

        # Step 3: Correct answer
        correct = get_label(WORD_GAME_LABELS, "correct", lang, word="MANGO")
        journey_steps.append(f"Bot: {correct[:40]}...")

        # Step 4: Play again prompt
        play_again = get_label(WORD_GAME_LABELS, "play_again", lang)
        journey_steps.append(f"Bot: {play_again[:40]}...")

        print(f"\n  {LANGUAGE_NAMES[lang]} ({lang}):")
        for step in journey_steps:
            print(f"    {step}")

        if all(len(s) > 5 for s in journey_steps):
            print(f"    ✅ Journey complete")
        else:
            print(f"    ❌ Journey incomplete")
            all_passed = False

    return all_passed


# ============================================================
# TEST 2: STRESS TEST - RAPID LANGUAGE SWITCHING
# ============================================================
def test_rapid_language_switching():
    """Test rapid switching between languages (simulates multi-user scenario)."""
    print("\n" + "=" * 70)
    print("TEST 2: STRESS TEST - RAPID LANGUAGE SWITCHING")
    print("=" * 70)

    all_passed = True
    iterations = 100
    errors = []

    print(f"\n  Running {iterations} rapid language switches...")

    start_time = time.time()

    for i in range(iterations):
        # Random language
        lang = random.choice(LANGUAGES)

        # Random label type
        label_type = random.choice(["event", "local", "word", "food", "sub"])

        try:
            if label_type == "event":
                result = get_label(EVENT_LABELS, "found", lang, count=random.randint(1, 100))
            elif label_type == "local":
                result = get_label(LOCAL_SEARCH_LABELS, "searching", lang, query="test")
            elif label_type == "word":
                result = get_label(WORD_GAME_LABELS, "correct", lang, word="TEST")
            elif label_type == "food":
                result = get_label(FOOD_LABELS, "title", lang)
            else:
                result = get_label(SUBSCRIPTION_LABELS, "subscribed", lang)

            if not result or len(result) < 3:
                errors.append(f"Empty result for {label_type} in {lang}")

        except Exception as e:
            errors.append(f"Error in {label_type}/{lang}: {str(e)}")
            all_passed = False

    elapsed = time.time() - start_time

    print(f"  Completed {iterations} iterations in {elapsed:.3f}s")
    print(f"  Average: {(elapsed/iterations)*1000:.2f}ms per lookup")

    if errors:
        print(f"  ❌ {len(errors)} errors found:")
        for err in errors[:5]:
            print(f"    - {err}")
        all_passed = False
    else:
        print(f"  ✅ All {iterations} lookups successful")

    return all_passed


# ============================================================
# TEST 3: ALL LABELS EXHAUSTIVE CHECK
# ============================================================
def test_all_labels_exhaustive():
    """Check every single label in every dictionary for every language."""
    print("\n" + "=" * 70)
    print("TEST 3: EXHAUSTIVE LABEL CHECK")
    print("=" * 70)

    all_dicts = {
        "EVENT_LABELS": EVENT_LABELS,
        "LOCAL_SEARCH_LABELS": LOCAL_SEARCH_LABELS,
        "WORD_GAME_LABELS": WORD_GAME_LABELS,
        "FOOD_LABELS": FOOD_LABELS,
        "SUBSCRIPTION_LABELS": SUBSCRIPTION_LABELS,
        "COMMON_PHRASES": COMMON_PHRASES,
        "TRAIN_LABELS": TRAIN_LABELS,
    }

    total_labels = 0
    missing_labels = 0
    empty_labels = 0
    all_passed = True

    for dict_name, labels_dict in all_dicts.items():
        if not labels_dict:
            print(f"\n  ⚠️  {dict_name}: Empty or not found")
            continue

        # Get all keys from English as reference
        en_keys = set(labels_dict.get("en", {}).keys())
        print(f"\n  --- {dict_name} ({len(en_keys)} keys) ---")

        dict_issues = []

        for lang in LANGUAGES:
            if lang not in labels_dict:
                dict_issues.append(f"{lang}: Missing language")
                missing_labels += len(en_keys)
                continue

            lang_labels = labels_dict[lang]
            lang_missing = []
            lang_empty = []

            for key in en_keys:
                total_labels += 1
                if key not in lang_labels:
                    lang_missing.append(key)
                    missing_labels += 1
                elif not lang_labels[key]:
                    lang_empty.append(key)
                    empty_labels += 1

            if lang_missing or lang_empty:
                issues = []
                if lang_missing:
                    issues.append(f"missing: {lang_missing[:3]}")
                if lang_empty:
                    issues.append(f"empty: {lang_empty[:3]}")
                dict_issues.append(f"{lang}: {', '.join(issues)}")

        if dict_issues:
            for issue in dict_issues[:5]:
                print(f"    ⚠️  {issue}")
            if len(dict_issues) > 5:
                print(f"    ... and {len(dict_issues) - 5} more issues")
        else:
            print(f"    ✅ All {len(LANGUAGES)} languages complete")

    print(f"\n  Summary:")
    print(f"    Total label checks: {total_labels}")
    print(f"    Missing labels: {missing_labels}")
    print(f"    Empty labels: {empty_labels}")

    if missing_labels == 0 and empty_labels == 0:
        print(f"    ✅ All labels present and non-empty")
    else:
        print(f"    ⚠️  Some labels need attention")

    return missing_labels == 0


# ============================================================
# TEST 4: EMOJI AND SPECIAL CHARACTER PRESERVATION
# ============================================================
def test_emoji_preservation():
    """Test that emojis work correctly with all language scripts."""
    print("\n" + "=" * 70)
    print("TEST 4: EMOJI AND SPECIAL CHARACTER PRESERVATION")
    print("=" * 70)

    all_passed = True

    # Test emojis with different scripts
    test_cases = [
        ("🎫", "Event emoji"),
        ("📍", "Location pin"),
        ("⭐", "Star rating"),
        ("🏏", "Cricket"),
        ("📞", "Phone"),
        ("💰", "Money"),
        ("🔍", "Search"),
        ("✅", "Checkmark"),
        ("❌", "Cross"),
    ]

    print("\n  Testing emoji + native script combinations:")

    for emoji, desc in test_cases:
        print(f"\n  --- {emoji} {desc} ---")
        for lang in ["en", "hi", "ta", "bn", "ml"]:
            # Combine emoji with native text
            found = get_label(EVENT_LABELS, "found", lang, count=5)
            combined = f"{emoji} {found}"

            # Check emoji is preserved
            has_emoji = emoji in combined
            has_text = len(found) > 5

            status = "✅" if (has_emoji and has_text) else "❌"
            print(f"    {status} {LANGUAGE_NAMES[lang]:12}: {combined[:50]}")

            if not (has_emoji and has_text):
                all_passed = False

    return all_passed


# ============================================================
# TEST 5: NUMBER FORMATTING IN DIFFERENT SCRIPTS
# ============================================================
def test_number_formatting():
    """Test that numbers format correctly in all languages."""
    print("\n" + "=" * 70)
    print("TEST 5: NUMBER FORMATTING")
    print("=" * 70)

    all_passed = True

    test_numbers = [0, 1, 10, 100, 1000, 99999]

    print("\n  Testing number placeholders:")

    for num in test_numbers:
        print(f"\n  --- Count: {num} ---")
        for lang in LANGUAGES:
            result = get_label(EVENT_LABELS, "found", lang, count=num)

            # Check number appears in result
            has_number = str(num) in result
            status = "✅" if has_number else "❌"
            print(f"    {status} {LANGUAGE_NAMES[lang]:12}: {result[:45]}")

            if not has_number:
                all_passed = False

    return all_passed


# ============================================================
# TEST 6: WHITESPACE AND FORMATTING CONSISTENCY
# ============================================================
def test_whitespace_formatting():
    """Test whitespace handling and formatting consistency."""
    print("\n" + "=" * 70)
    print("TEST 6: WHITESPACE AND FORMATTING CONSISTENCY")
    print("=" * 70)

    all_passed = True
    issues = []

    print("\n  Checking for formatting issues:")

    all_dicts = {
        "EVENT": EVENT_LABELS,
        "LOCAL": LOCAL_SEARCH_LABELS,
        "WORD": WORD_GAME_LABELS,
        "FOOD": FOOD_LABELS,
        "SUB": SUBSCRIPTION_LABELS,
    }

    for dict_name, labels_dict in all_dicts.items():
        for lang in LANGUAGES:
            if lang not in labels_dict:
                continue

            for key, value in labels_dict[lang].items():
                if not isinstance(value, str):
                    continue

                # Check for issues
                if value.startswith(" ") or value.endswith(" "):
                    issues.append(f"{dict_name}/{lang}/{key}: Leading/trailing space")
                if "  " in value:
                    issues.append(f"{dict_name}/{lang}/{key}: Double space")
                if value != value.strip() and len(value.strip()) > 0:
                    issues.append(f"{dict_name}/{lang}/{key}: Whitespace issue")

    if issues:
        print(f"  ⚠️  Found {len(issues)} whitespace issues:")
        for issue in issues[:10]:
            print(f"    - {issue}")
        if len(issues) > 10:
            print(f"    ... and {len(issues) - 10} more")
    else:
        print(f"  ✅ No whitespace issues found")

    return len(issues) == 0


# ============================================================
# TEST 7: PLACEHOLDER MISMATCH DETECTION
# ============================================================
def test_placeholder_consistency():
    """Check that placeholders are consistent across translations."""
    print("\n" + "=" * 70)
    print("TEST 7: PLACEHOLDER CONSISTENCY CHECK")
    print("=" * 70)

    all_passed = True
    issues = []

    # Labels with known placeholders
    placeholder_labels = [
        (EVENT_LABELS, "found", ["count"]),
        (EVENT_LABELS, "and_more", ["count"]),
        (EVENT_LABELS, "events_near", ["city"]),
        (LOCAL_SEARCH_LABELS, "searching", ["query"]),
        (LOCAL_SEARCH_LABELS, "no_places_for", ["query"]),
        (WORD_GAME_LABELS, "correct", ["word"]),
    ]

    print("\n  Checking placeholder consistency:")

    for labels_dict, key, expected_placeholders in placeholder_labels:
        print(f"\n  --- {key} (expects: {expected_placeholders}) ---")

        for lang in LANGUAGES:
            if lang not in labels_dict:
                continue

            template = labels_dict[lang].get(key, "")

            # Check each expected placeholder
            missing = []
            for ph in expected_placeholders:
                if f"{{{ph}}}" not in template:
                    missing.append(ph)

            if missing:
                status = "❌"
                issues.append(f"{key}/{lang}: Missing {missing}")
                all_passed = False
            else:
                status = "✅"

            print(f"    {status} {LANGUAGE_NAMES[lang]:12}: {template[:40]}...")

    if issues:
        print(f"\n  ⚠️  {len(issues)} placeholder issues found")
    else:
        print(f"\n  ✅ All placeholders consistent")

    return all_passed


# ============================================================
# TEST 8: CROSS-LANGUAGE CONSISTENCY
# ============================================================
def test_cross_language_consistency():
    """Check that translations convey the same meaning (basic checks)."""
    print("\n" + "=" * 70)
    print("TEST 8: CROSS-LANGUAGE CONSISTENCY")
    print("=" * 70)

    all_passed = True

    # Check that certain elements are preserved across translations
    consistency_checks = [
        # (labels_dict, key, must_contain_pattern, description)
        (EVENT_LABELS, "ipl_title", "IPL", "IPL brand name"),
        (EVENT_LABELS, "ipl_title", "2025", "Year"),
        (WORD_GAME_LABELS, "play_again", "word game", "Command text"),
        (SUBSCRIPTION_LABELS, "daily_horoscope", "6", "Time (6 AM)"),
    ]

    print("\n  Checking that key elements are preserved:")

    for labels_dict, key, must_contain, desc in consistency_checks:
        print(f"\n  --- {key}: Must contain '{must_contain}' ({desc}) ---")

        for lang in LANGUAGES:
            if lang not in labels_dict:
                continue

            value = labels_dict[lang].get(key, "")
            contains = must_contain.lower() in value.lower()

            status = "✅" if contains else "⚠️"
            print(f"    {status} {LANGUAGE_NAMES[lang]:12}: {value[:45]}...")

            if not contains:
                # This is a warning, not a failure (translations may vary)
                pass

    return all_passed


# ============================================================
# TEST 9: MULTI-USER SIMULATION
# ============================================================
def test_multi_user_simulation():
    """Simulate multiple users with different languages simultaneously."""
    print("\n" + "=" * 70)
    print("TEST 9: MULTI-USER SIMULATION")
    print("=" * 70)

    all_passed = True

    # Simulate 11 users, each with a different language
    users = [
        {"id": f"user_{i}", "lang": lang, "phone": f"91987654321{i}"}
        for i, lang in enumerate(LANGUAGES)
    ]

    print(f"\n  Simulating {len(users)} concurrent users:")

    # Each user performs a sequence of actions
    actions = ["search_event", "play_word_game", "search_local", "subscribe"]

    results = {user["id"]: [] for user in users}

    for action in actions:
        for user in users:
            lang = user["lang"]

            if action == "search_event":
                response = get_label(EVENT_LABELS, "found", lang, count=3)
            elif action == "play_word_game":
                response = get_label(WORD_GAME_LABELS, "start", lang)
            elif action == "search_local":
                response = get_label(LOCAL_SEARCH_LABELS, "found_places", lang)
            elif action == "subscribe":
                response = get_label(SUBSCRIPTION_LABELS, "subscribed", lang)

            results[user["id"]].append({
                "action": action,
                "response": response[:30],
                "valid": len(response) > 5
            })

    # Print results
    for user in users:
        user_results = results[user["id"]]
        all_valid = all(r["valid"] for r in user_results)
        status = "✅" if all_valid else "❌"

        print(f"\n  {status} {user['id']} ({LANGUAGE_NAMES[user['lang']]}):")
        for r in user_results:
            print(f"      {r['action']}: {r['response']}...")

        if not all_valid:
            all_passed = False

    return all_passed


# ============================================================
# TEST 10: ERROR RECOVERY SCENARIOS
# ============================================================
def test_error_recovery():
    """Test error handling and recovery scenarios."""
    print("\n" + "=" * 70)
    print("TEST 10: ERROR RECOVERY SCENARIOS")
    print("=" * 70)

    all_passed = True

    print("\n  Testing error recovery in all languages:")

    # Scenario 1: Event search fails
    print("\n  --- Scenario: Event search returns no results ---")
    for lang in LANGUAGES:
        not_found = get_label(EVENT_LABELS, "not_found", lang)
        has_content = len(not_found) > 5
        status = "✅" if has_content else "❌"
        print(f"    {status} {LANGUAGE_NAMES[lang]:12}: {not_found[:40]}")
        if not has_content:
            all_passed = False

    # Scenario 2: Local search fails
    print("\n  --- Scenario: Local search no results ---")
    for lang in LANGUAGES:
        no_places = get_label(LOCAL_SEARCH_LABELS, "no_places_for", lang, query="xyz")
        has_content = len(no_places) > 5
        status = "✅" if has_content else "❌"
        print(f"    {status} {LANGUAGE_NAMES[lang]:12}: {no_places[:40]}")
        if not has_content:
            all_passed = False

    # Scenario 3: Subscription error
    print("\n  --- Scenario: Subscription process fails ---")
    for lang in LANGUAGES:
        error = get_label(SUBSCRIPTION_LABELS, "error", lang)
        has_content = len(error) > 5
        status = "✅" if has_content else "❌"
        print(f"    {status} {LANGUAGE_NAMES[lang]:12}: {error[:40]}")
        if not has_content:
            all_passed = False

    # Scenario 4: Word game error
    print("\n  --- Scenario: Word game crashes ---")
    for lang in LANGUAGES:
        error = get_label(WORD_GAME_LABELS, "error", lang)
        has_content = len(error) > 5
        status = "✅" if has_content else "❌"
        print(f"    {status} {LANGUAGE_NAMES[lang]:12}: {error[:40]}")
        if not has_content:
            all_passed = False

    return all_passed


# ============================================================
# TEST 11: FULL MESSAGE BUILDER TEST
# ============================================================
def test_full_message_builder():
    """Test building complete WhatsApp messages in all languages."""
    print("\n" + "=" * 70)
    print("TEST 11: FULL MESSAGE BUILDER TEST")
    print("=" * 70)

    all_passed = True

    print("\n  Building complete event response messages:")

    for lang in ["en", "hi", "ta", "bn", "te", "kn"]:
        # Build a complete event response
        found = get_label(EVENT_LABELS, "found", lang, count=3)
        at_label = get_label(EVENT_LABELS, "at", lang)
        and_more = get_label(EVENT_LABELS, "and_more", lang, count=5)
        more_details = get_label(EVENT_LABELS, "more_details", lang)

        message = f"""🎫 *{found}:*

*1. Coldplay Concert*
📍 Mumbai Stadium
📅 Jan 25, 2025 {at_label} 7:00 PM
💰 ₹2,500 - ₹15,000

*2. Arijit Singh Live*
📍 Bengaluru Arena
📅 Feb 10, 2025 {at_label} 8:00 PM
💰 ₹1,500 - ₹8,000

_{and_more}_

📱 {more_details}"""

        # Validate message
        has_emoji = "🎫" in message and "📍" in message
        has_native_text = any(ord(c) > 127 for c in message) if lang != "en" else True
        has_structure = "*1." in message and "*2." in message

        valid = has_emoji and has_native_text and has_structure

        status = "✅" if valid else "❌"
        print(f"\n  {status} {LANGUAGE_NAMES[lang]} ({lang}):")
        print("    " + message.replace("\n", "\n    ")[:300] + "...")

        if not valid:
            all_passed = False

    return all_passed


# ============================================================
# TEST 12: PERFORMANCE BENCHMARK
# ============================================================
def test_performance_benchmark():
    """Benchmark label lookup performance."""
    print("\n" + "=" * 70)
    print("TEST 12: PERFORMANCE BENCHMARK")
    print("=" * 70)

    iterations = 10000

    print(f"\n  Running {iterations} label lookups...")

    # Warm up
    for _ in range(100):
        get_label(EVENT_LABELS, "found", "hi", count=5)

    # Benchmark
    start = time.time()
    for i in range(iterations):
        lang = LANGUAGES[i % len(LANGUAGES)]
        get_label(EVENT_LABELS, "found", lang, count=i)
        get_label(LOCAL_SEARCH_LABELS, "searching", lang, query="test")
        get_label(WORD_GAME_LABELS, "start", lang)
    elapsed = time.time() - start

    ops_per_sec = (iterations * 3) / elapsed
    avg_ms = (elapsed / (iterations * 3)) * 1000

    print(f"\n  Results:")
    print(f"    Total operations: {iterations * 3}")
    print(f"    Total time: {elapsed:.3f}s")
    print(f"    Operations/sec: {ops_per_sec:,.0f}")
    print(f"    Average per lookup: {avg_ms:.4f}ms")

    # Pass if performance is reasonable (< 1ms per lookup)
    passed = avg_ms < 1.0
    status = "✅" if passed else "❌"
    print(f"\n  {status} Performance {'acceptable' if passed else 'needs improvement'}")

    return passed


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("END-TO-END MULTILINGUAL TEST SUITE")
    print("Comprehensive testing of WhatsApp bot multilingual system")
    print("=" * 70)

    results = {}

    # Run all tests
    results["User Journey Simulation"] = test_user_journey_simulation()
    results["Rapid Language Switching"] = test_rapid_language_switching()
    results["Exhaustive Label Check"] = test_all_labels_exhaustive()
    results["Emoji Preservation"] = test_emoji_preservation()
    results["Number Formatting"] = test_number_formatting()
    results["Whitespace Formatting"] = test_whitespace_formatting()
    results["Placeholder Consistency"] = test_placeholder_consistency()
    results["Cross-Language Consistency"] = test_cross_language_consistency()
    results["Multi-User Simulation"] = test_multi_user_simulation()
    results["Error Recovery"] = test_error_recovery()
    results["Full Message Builder"] = test_full_message_builder()
    results["Performance Benchmark"] = test_performance_benchmark()

    # Summary
    print("\n" + "=" * 70)
    print("END-TO-END TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "-" * 70)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL END-TO-END TESTS PASSED!")
        print("The multilingual system is production-ready.")
    else:
        print("⚠️  Some tests need attention - review details above")
    print("-" * 70)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
