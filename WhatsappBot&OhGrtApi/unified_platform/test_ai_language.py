"""
Test script for AI-based language understanding service.

Tests:
1. Language detection
2. Intent understanding
3. Entity extraction (with English normalization)
4. Response translation
"""

import asyncio
import sys
sys.path.insert(0, "/Users/rishi/Desktop/WorkSpace/AIBot/WhatsappBot&OhGrtApi/unified_platform")

from common.services.ai_language_service import (
    AILanguageService,
    ai_understand_message,
    ai_translate_response,
    init_ai_language_service,
)

# Test messages in different languages
TEST_MESSAGES = [
    # Hindi weather queries
    ("दिल्ली का मौसम बताओ", "hi", "weather", {"city": "Delhi"}),
    ("मुंबई में आज मौसम कैसा है", "hi", "weather", {"city": "Mumbai"}),

    # Tamil weather queries
    ("சென்னை வானிலை", "ta", "weather", {"city": "Chennai"}),

    # Telugu weather queries
    ("హైదరాబాద్ వాతావరణం ఎలా ఉంది", "te", "weather", {"city": "Hyderabad"}),

    # Bengali weather queries
    ("কলকাতার আবহাওয়া কেমন", "bn", "weather", {"city": "Kolkata"}),

    # Kannada weather queries
    ("ಬೆಂಗಳೂರಿನ ಹವಾಮಾನ", "kn", "weather", {"city": "Bengaluru"}),

    # Punjabi weather queries
    ("ਅੰਮ੍ਰਿਤਸਰ ਦਾ ਮੌਸਮ", "pa", "weather", {"city": "Amritsar"}),

    # English weather queries
    ("weather in London", "en", "weather", {"city": "London"}),
    ("What's the temperature in New York", "en", "weather", {"city": "New York"}),

    # Hindi local search
    ("दिल्ली में रेस्टोरेंट", "hi", "local_search", {"location": "Delhi"}),

    # Hindi horoscope
    ("मेष राशिफल", "hi", "get_horoscope", {"astro_sign": "Aries"}),

    # English help
    ("what can you do", "en", "help", {}),

    # Hindi help
    ("तुम क्या कर सकते हो", "hi", "help", {}),
]

# Test translation
TEST_TRANSLATIONS = [
    ("Weather in Delhi: 25°C, Sunny, Humidity: 60%", "hi"),
    ("Weather in Mumbai: 30°C, Cloudy, Humidity: 80%", "ta"),
    ("Weather in Chennai: 28°C, Light Rain, Humidity: 75%", "te"),
]


async def test_language_understanding():
    """Test language understanding for various messages."""
    print("=" * 70)
    print("AI LANGUAGE UNDERSTANDING TEST")
    print("=" * 70)

    # Check if OpenAI API key is available
    try:
        from whatsapp_bot.config import settings
        api_key = settings.openai_api_key
        if not api_key:
            print("ERROR: OpenAI API key not found in settings")
            return False
    except Exception as e:
        print(f"ERROR: Failed to load settings: {e}")
        return False

    # Initialize the service
    init_ai_language_service(api_key)

    passed = 0
    failed = 0

    for message, expected_lang, expected_intent, expected_entities in TEST_MESSAGES:
        print(f"\n--- Testing: {message[:50]}... ---")

        try:
            result = await ai_understand_message(message, api_key)

            detected_lang = result.get("detected_language", "")
            intent = result.get("intent", "")
            entities = result.get("entities", {})

            # Check language
            lang_ok = detected_lang == expected_lang
            # Check intent
            intent_ok = intent == expected_intent
            # Check entities (if expected)
            entities_ok = True
            for key, value in expected_entities.items():
                if key not in entities or entities[key] != value:
                    entities_ok = False
                    break

            if lang_ok and intent_ok and entities_ok:
                print(f"  ✅ PASS")
                print(f"     Lang: {detected_lang} | Intent: {intent} | Entities: {entities}")
                passed += 1
            else:
                print(f"  ❌ FAIL")
                print(f"     Expected: lang={expected_lang}, intent={expected_intent}, entities={expected_entities}")
                print(f"     Got:      lang={detected_lang}, intent={intent}, entities={entities}")
                failed += 1

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


async def test_translation():
    """Test translation of responses."""
    print("\n" + "=" * 70)
    print("AI TRANSLATION TEST")
    print("=" * 70)

    try:
        from whatsapp_bot.config import settings
        api_key = settings.openai_api_key
    except Exception as e:
        print(f"ERROR: Failed to load settings: {e}")
        return False

    for text, target_lang in TEST_TRANSLATIONS:
        print(f"\n--- Translating to {target_lang}: {text[:50]}... ---")

        try:
            translated = await ai_translate_response(text, target_lang, api_key)
            print(f"  Original: {text}")
            print(f"  Translated ({target_lang}): {translated}")
        except Exception as e:
            print(f"  ERROR: {e}")

    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("AI LANGUAGE SERVICE TEST SUITE")
    print("=" * 70)

    # Test understanding
    understanding_ok = await test_language_understanding()

    # Test translation
    translation_ok = await test_translation()

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Language Understanding: {'✅ PASS' if understanding_ok else '❌ FAIL'}")
    print(f"Translation: {'✅ PASS' if translation_ok else '❌ FAIL'}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
