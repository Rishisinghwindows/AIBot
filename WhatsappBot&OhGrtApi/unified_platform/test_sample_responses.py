"""
Sample response generator for all languages.
Shows how responses look in each of the 11 supported languages.
"""

import sys
sys.path.insert(0, "/Users/rishi/Desktop/WorkSpace/AIBot/WhatsappBot&OhGrtApi/unified_platform")

# Read responses.py directly
responses_path = "/Users/rishi/Desktop/WorkSpace/AIBot/WhatsappBot&OhGrtApi/unified_platform/common/i18n/responses.py"
with open(responses_path, 'r') as f:
    content = f.read()

exec_globals = {}
exec(content, exec_globals)

WORD_GAME_LABELS = exec_globals.get('WORD_GAME_LABELS', {})
EVENT_LABELS = exec_globals.get('EVENT_LABELS', {})
LOCAL_SEARCH_LABELS = exec_globals.get('LOCAL_SEARCH_LABELS', {})

LANGUAGES = ["en", "hi", "bn", "ta", "te", "kn", "ml", "gu", "mr", "pa", "or"]
LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu", "kn": "Kannada", "ml": "Malayalam", "gu": "Gujarati",
    "mr": "Marathi", "pa": "Punjabi", "or": "Odia",
}


def format_events_response_sample(lang: str) -> str:
    """Generate a sample events response in the given language."""
    labels = EVENT_LABELS.get(lang, EVENT_LABELS["en"])

    found = labels.get("found", "Found {count} events").format(count=3)
    at = labels.get("at", "at")
    and_more = labels.get("and_more", "...and {count} more").format(count=2)
    more_details = labels.get("more_details", "Reply with the event number for more details!")

    response = f"""🎫 *{found}:*

*1. Coldplay Music of the Spheres World Tour*
📍 DY Patil Stadium, Mumbai
📅 January 21, 2025 {at} 7:00 PM
💰 ₹2,500 - ₹35,000

*2. Sunburn Festival 2025*
📍 Vagator Beach, Goa
📅 December 28, 2024 {at} 4:00 PM
💰 ₹3,500 - ₹15,000

*3. Zakir Khan Live*
📍 Phoenix Marketcity, Bengaluru
📅 February 15, 2025 {at} 8:00 PM
💰 ₹999 - ₹2,999

_{and_more}_

📱 {more_details}"""

    return response


def format_ipl_response_sample(lang: str) -> str:
    """Generate a sample IPL response in the given language."""
    labels = EVENT_LABELS.get(lang, EVENT_LABELS["en"])

    ipl_title = labels.get("ipl_title", "IPL 2025 Matches")
    at = labels.get("at", "at")
    ticket_details = labels.get("ticket_details", "Reply with match number for ticket details!")

    response = f"""🏏 *{ipl_title}:*

*1. Royal Challengers Bengaluru vs Chennai Super Kings*
📍 M. Chinnaswamy Stadium, Bengaluru
📅 March 22, 2025 {at} 7:30 PM
💰 ₹800 - ₹25,000

*2. Mumbai Indians vs Kolkata Knight Riders*
📍 Wankhede Stadium, Mumbai
📅 March 25, 2025 {at} 7:30 PM
💰 ₹750 - ₹22,000

🎟️ {ticket_details}"""

    return response


def format_local_search_sample(lang: str) -> str:
    """Generate a sample local search response in the given language."""
    labels = LOCAL_SEARCH_LABELS.get(lang, LOCAL_SEARCH_LABELS["en"])

    found_places = labels.get("found_places", "Found these places")
    away = labels.get("away", "away")
    reviews = labels.get("reviews", "reviews")

    response = f"""*Restaurants near Koramangala*

*{found_places}:*

1. *Toit Brewpub*
   _Microbrewery_
   📏 0.3 km {away}
   📍 100 Feet Road, Koramangala
   ⭐⭐⭐⭐ 4.5 (2,450 {reviews})
   📞 +91 80 4117 1234

2. *Truffles*
   _American Restaurant_
   📏 0.5 km {away}
   📍 St. Johns Road, Koramangala
   ⭐⭐⭐⭐ 4.3 (3,200 {reviews})
   📞 +91 80 2556 7890

3. *Empire Restaurant*
   _North Indian_
   📏 0.8 km {away}
   📍 Church Street, Koramangala
   ⭐⭐⭐⭐ 4.1 (5,600 {reviews})
   📞 +91 80 4112 3456"""

    return response


def format_word_game_sample(lang: str) -> str:
    """Generate a sample word game response in the given language."""
    labels = WORD_GAME_LABELS.get(lang, WORD_GAME_LABELS["en"])

    start = labels.get("start", "Let's play a word game! Unscramble this word:")

    response = f"""{start}

*PPAELNIS*"""

    return response


def format_word_game_correct_sample(lang: str) -> str:
    """Generate a sample word game correct response in the given language."""
    labels = WORD_GAME_LABELS.get(lang, WORD_GAME_LABELS["en"])

    correct = labels.get("correct", "Correct! The word was *{word}*. Well done!").format(word="PINEAPPLE")
    play_again = labels.get("play_again", "Type 'word game' to play again.")

    response = f"""{correct}

{play_again}"""

    return response


def main():
    print("="*70)
    print("SAMPLE RESPONSES IN ALL 11 LANGUAGES")
    print("="*70)

    # Select a few key languages to show samples
    sample_langs = ["en", "hi", "ta", "bn", "kn"]

    print("\n" + "="*70)
    print("1. WORD GAME - Start")
    print("="*70)
    for lang in sample_langs:
        print(f"\n--- {LANGUAGE_NAMES[lang]} ({lang}) ---")
        print(format_word_game_sample(lang))

    print("\n" + "="*70)
    print("2. WORD GAME - Correct Answer")
    print("="*70)
    for lang in sample_langs:
        print(f"\n--- {LANGUAGE_NAMES[lang]} ({lang}) ---")
        print(format_word_game_correct_sample(lang))

    print("\n" + "="*70)
    print("3. EVENTS - Found Events")
    print("="*70)
    for lang in sample_langs:
        print(f"\n--- {LANGUAGE_NAMES[lang]} ({lang}) ---")
        print(format_events_response_sample(lang))

    print("\n" + "="*70)
    print("4. IPL MATCHES")
    print("="*70)
    for lang in sample_langs:
        print(f"\n--- {LANGUAGE_NAMES[lang]} ({lang}) ---")
        print(format_ipl_response_sample(lang))

    print("\n" + "="*70)
    print("5. LOCAL SEARCH - Restaurants")
    print("="*70)
    for lang in sample_langs:
        print(f"\n--- {LANGUAGE_NAMES[lang]} ({lang}) ---")
        print(format_local_search_sample(lang))

    print("\n" + "="*70)
    print("ALL SAMPLE RESPONSES GENERATED SUCCESSFULLY!")
    print("="*70)


if __name__ == "__main__":
    main()
