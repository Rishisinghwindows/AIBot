"""
Travel Node

Handles Indian Railways features:
- PNR Status
- Train Running Status (with detailed emoji format)

Uses the OhGrtApi TravelService with web scraper fallback.
"""

import re
from datetime import datetime
from app.graph.state import BotState
from app.services.travel_service import get_travel_service
from app.services.train_scraper import scrape_train_status_detailed, scrape_train_status
from app.config import get_settings
from app.logger import logger

PNR_INTENT = "pnr_status"
TRAIN_INTENT = "train_status"

# Hindi labels for the detailed format
HINDI_LABELS = {
    "train_details": "ट्रेन के विवरण हिंदी में:",
    "train": "🚆",
    "route": "📍 शुरुआत:",
    "travel_date": "🗓️ यात्रा तिथि:",
    "scheduled_departure": "⏱️ निर्धारित रवानगी:",
    "last_update": "🔄 अंतिम अपडेट:",
    "current": "📊 वर्तमान:",
    "platform": "प्लेटफॉर्म",
    "platform_unknown": "अज्ञात",
    "arrival_time": "आगमन समय:",
    "departure_time": "प्रस्थान समय:",
    "status": "⏰ स्थिति:",
    "delay_suffix": "(कुछ सेकंड पहले)",
    "distance": "📏 दूरी:",
    "distance_format": "मूल से {traveled}/{total} किमी",
    "next_stations": "अगले स्टेशन:",
    "fetched_at": "डेटा प्राप्त किया गया समय:",
    "from_to": "से",
    "for": "के लिए",
    "on_time": "समय पर",
    "minutes_late": "मिनट की देरी",
    "minutes_early": "मिनट पहले",
}

# English labels
ENGLISH_LABELS = {
    "train_details": "Train Details:",
    "train": "🚆",
    "route": "📍 Route:",
    "travel_date": "🗓️ Travel Date:",
    "scheduled_departure": "⏱️ Scheduled Departure:",
    "last_update": "🔄 Last Update:",
    "current": "📊 Current:",
    "platform": "Platform",
    "platform_unknown": "Unknown",
    "arrival_time": "Arrival:",
    "departure_time": "Departure:",
    "status": "⏰ Status:",
    "delay_suffix": "(just now)",
    "distance": "📏 Distance:",
    "distance_format": "{traveled}/{total} km from origin",
    "next_stations": "Next Stations:",
    "fetched_at": "Data fetched at:",
    "from_to": "to",
    "for": "for",
    "on_time": "On Time",
    "minutes_late": "minutes late",
    "minutes_early": "minutes early",
}

# Kannada labels
KANNADA_LABELS = {
    "train_details": "ರೈಲು ವಿವರಗಳು:",
    "train": "🚆",
    "route": "📍 ಮಾರ್ಗ:",
    "travel_date": "🗓️ ಪ್ರಯಾಣ ದಿನಾಂಕ:",
    "scheduled_departure": "⏱️ ನಿಗದಿತ ಹೊರಡುವಿಕೆ:",
    "last_update": "🔄 ಕೊನೆಯ ನವೀಕರಣ:",
    "current": "📊 ಪ್ರಸ್ತುತ:",
    "platform": "ಪ್ಲಾಟ್‌ಫಾರ್ಮ್",
    "platform_unknown": "ತಿಳಿದಿಲ್ಲ",
    "arrival_time": "ಆಗಮನ:",
    "departure_time": "ನಿರ್ಗಮನ:",
    "status": "⏰ ಸ್ಥಿತಿ:",
    "delay_suffix": "(ಈಗಷ್ಟೇ)",
    "distance": "📏 ದೂರ:",
    "distance_format": "ಮೂಲದಿಂದ {traveled}/{total} ಕಿಮೀ",
    "next_stations": "ಮುಂದಿನ ನಿಲ್ದಾಣಗಳು:",
    "fetched_at": "ಡೇಟಾ ಪಡೆದ ಸಮಯ:",
    "from_to": "ರಿಂದ",
    "for": "ಗೆ",
    "on_time": "ಸಮಯಕ್ಕೆ ಸರಿಯಾಗಿ",
    "minutes_late": "ನಿಮಿಷ ತಡವಾಗಿ",
    "minutes_early": "ನಿಮಿಷ ಮುಂಚೆ",
}

# Tamil labels
TAMIL_LABELS = {
    "train_details": "ரயில் விவரங்கள்:",
    "train": "🚆",
    "route": "📍 பாதை:",
    "travel_date": "🗓️ பயண தேதி:",
    "scheduled_departure": "⏱️ திட்டமிட்ட புறப்பாடு:",
    "last_update": "🔄 கடைசி புதுப்பிப்பு:",
    "current": "📊 தற்போதைய:",
    "platform": "தளம்",
    "platform_unknown": "தெரியவில்லை",
    "arrival_time": "வருகை:",
    "departure_time": "புறப்படல்:",
    "status": "⏰ நிலை:",
    "delay_suffix": "(இப்போது)",
    "distance": "📏 தூரம்:",
    "distance_format": "தொடக்கத்திலிருந்து {traveled}/{total} கி.மீ",
    "next_stations": "அடுத்த நிலையங்கள்:",
    "fetched_at": "தரவு பெறப்பட்ட நேரம்:",
    "from_to": "இருந்து",
    "for": "வரை",
    "on_time": "சரியான நேரத்தில்",
    "minutes_late": "நிமிடங்கள் தாமதம்",
    "minutes_early": "நிமிடங்கள் முன்னதாக",
}

# Telugu labels
TELUGU_LABELS = {
    "train_details": "రైలు వివరాలు:",
    "train": "🚆",
    "route": "📍 మార్గం:",
    "travel_date": "🗓️ ప్రయాణ తేదీ:",
    "scheduled_departure": "⏱️ షెడ్యూల్డ్ బయలుదేరడం:",
    "last_update": "🔄 చివరి అప్‌డేట్:",
    "current": "📊 ప్రస్తుత:",
    "platform": "ప్లాట్‌ఫారమ్",
    "platform_unknown": "తెలియదు",
    "arrival_time": "రాక:",
    "departure_time": "బయలుదేరడం:",
    "status": "⏰ స్థితి:",
    "delay_suffix": "(ఇప్పుడే)",
    "distance": "📏 దూరం:",
    "distance_format": "మూలం నుండి {traveled}/{total} కి.మీ",
    "next_stations": "తదుపరి స్టేషన్లు:",
    "fetched_at": "డేటా పొందిన సమయం:",
    "from_to": "నుండి",
    "for": "వరకు",
    "on_time": "సమయానికి",
    "minutes_late": "నిమిషాలు ఆలస్యం",
    "minutes_early": "నిమిషాలు ముందు",
}


def extract_pnr(text: str) -> str:
    """Extract 10-digit PNR number from text."""
    match = re.search(r'\b(\d{10})\b', text)
    return match.group(1) if match else ""


def extract_train_number(text: str) -> str:
    """Extract 4-5 digit train number from text."""
    match = re.search(r'\b(\d{4,5})\b', text)
    return match.group(1) if match else ""


def detect_requested_language(query: str, detected_lang: str = "en") -> str:
    """Detect language from query text - checks script and keywords."""
    query_lower = query.lower()

    # First check for explicit language keywords
    language_keywords = {
        "hi": ["hindi", "हिंदी", "हिन्दी", "में"],
        "kn": ["kannada", "ಕನ್ನಡ"],
        "ta": ["tamil", "தமிழ்"],
        "te": ["telugu", "తెలుగు"],
        "bn": ["bengali", "বাংলা", "bangla"],
        "mr": ["marathi", "मराठी"],
        "or": ["odia", "ଓଡ଼ିଆ", "oriya"],
        "en": ["english", "in english"],
    }

    for lang_code, keywords in language_keywords.items():
        for kw in keywords:
            if kw in query_lower or kw in query:
                return lang_code

    # Detect language from script (Unicode ranges)
    # Kannada: U+0C80 to U+0CFF
    if any('\u0C80' <= c <= '\u0CFF' for c in query):
        return "kn"
    # Hindi/Devanagari: U+0900 to U+097F
    if any('\u0900' <= c <= '\u097F' for c in query):
        return "hi"
    # Tamil: U+0B80 to U+0BFF
    if any('\u0B80' <= c <= '\u0BFF' for c in query):
        return "ta"
    # Telugu: U+0C00 to U+0C7F
    if any('\u0C00' <= c <= '\u0C7F' for c in query):
        return "te"
    # Bengali: U+0980 to U+09FF
    if any('\u0980' <= c <= '\u09FF' for c in query):
        return "bn"
    # Gujarati: U+0A80 to U+0AFF
    if any('\u0A80' <= c <= '\u0AFF' for c in query):
        return "gu"
    # Malayalam: U+0D00 to U+0D7F
    if any('\u0D00' <= c <= '\u0D7F' for c in query):
        return "ml"
    # Punjabi/Gurmukhi: U+0A00 to U+0A7F
    if any('\u0A00' <= c <= '\u0A7F' for c in query):
        return "pa"
    # Odia: U+0B00 to U+0B7F
    if any('\u0B00' <= c <= '\u0B7F' for c in query):
        return "or"
    # Marathi uses Devanagari, so it's covered by Hindi check above

    return detected_lang


def format_detailed_train_status(data: dict, lang: str = "hi") -> str:
    """
    Format train status data in detailed emoji format.

    Args:
        data: Train status data from scraper
        lang: Language code (hi for Hindi, en for English, kn for Kannada)

    Returns:
        Formatted message with emojis
    """
    if not data:
        if lang == "hi":
            return "ट्रेन की स्थिति प्राप्त नहीं हो सकी। कृपया ट्रेन नंबर जांचें।"
        elif lang == "kn":
            return "ರೈಲು ಸ್ಥಿತಿ ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ರೈಲು ಸಂಖ್ಯೆಯನ್ನು ಪರಿಶೀಲಿಸಿ."
        elif lang == "ta":
            return "ரயில் நிலையைப் பெற முடியவில்லை. தயவுசெய்து ரயில் எண்ணைச் சரிபார்க்கவும்."
        elif lang == "te":
            return "రైలు స్థితిని పొందలేకపోయాము. దయచేసి రైలు నంబర్ తనిఖీ చేయండి."
        return "Could not fetch train status. Please check the train number."

    # Select labels based on language
    if lang == "hi":
        labels = HINDI_LABELS
    elif lang == "kn":
        labels = KANNADA_LABELS
    elif lang == "ta":
        labels = TAMIL_LABELS
    elif lang == "te":
        labels = TELUGU_LABELS
    else:
        labels = ENGLISH_LABELS

    train_name = data.get("train_name", "Unknown")
    train_number = data.get("train_number", "")
    source = data.get("source", "")
    destination = data.get("destination", "")
    travel_date = data.get("travel_date", datetime.now().strftime("%Y-%m-%d"))
    scheduled_departure = data.get("scheduled_departure", "")
    last_update = data.get("last_update", "")
    current_station = data.get("current_station", data.get("last_station", "N/A"))
    current_code = data.get("current_station_code", "")
    current_platform = data.get("current_platform", labels["platform_unknown"])
    current_arrival = data.get("current_arrival", data.get("last_station_time", ""))
    current_departure = data.get("current_departure", "")
    delay_minutes = data.get("delay_minutes", 0)
    distance_traveled = data.get("distance_traveled", 0)
    total_distance = data.get("total_distance", 0)
    next_stations = data.get("next_stations", [])
    fetched_at = data.get("fetched_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"))

    # Format delay status
    if delay_minutes == 0:
        status_text = labels["on_time"]
    elif delay_minutes > 0:
        status_text = f"{delay_minutes} {labels['minutes_late']} {labels['delay_suffix']}"
    else:
        status_text = f"{abs(delay_minutes)} {labels['minutes_early']}"

    # Build message
    lines = []

    # Header with train number
    lines.append(f"{train_number} {labels['train_details']}\n")

    # Train name
    lines.append(f"{labels['train']} {train_name} ({train_number})")

    # Route
    if source and destination:
        lines.append(f"{labels['route']} {source} {labels['from_to']} {destination} {labels['for']}")

    # Travel date
    lines.append(f"{labels['travel_date']} {travel_date}")

    # Scheduled departure
    if scheduled_departure:
        lines.append(f"{labels['scheduled_departure']} {travel_date} {scheduled_departure}")

    # Last update
    if last_update:
        lines.append(f"{labels['last_update']} {last_update}")

    # Current station
    current_display = f"{current_station}"
    if current_code:
        current_display += f"~ ({current_code})"
    platform_text = current_platform if current_platform else labels["platform_unknown"]
    lines.append(f"{labels['current']} {current_display}, {labels['platform']} {platform_text}")

    # Arrival/Departure times at current station
    if current_arrival or current_departure:
        arr_time = current_arrival if current_arrival else "-"
        dep_time = current_departure if current_departure else "-"
        lines.append(f"⏳ {labels['arrival_time']} {arr_time}, {labels['departure_time']} {dep_time}")

    # Status with delay
    lines.append(f"{labels['status']} {status_text}")

    # Distance
    if distance_traveled > 0 and total_distance > 0:
        dist_text = labels['distance_format'].format(traveled=distance_traveled, total=total_distance)
        lines.append(f"{labels['distance']} {dist_text}")

    # Next stations
    if next_stations:
        lines.append(f"\n{labels['next_stations']}")

        for station in next_stations[:6]:
            name = station.get("name", "")
            code = station.get("code", "")
            arrival = station.get("arrival", "-")
            departure = station.get("departure", "-")
            platform = station.get("platform", "")

            if not name:
                continue

            # Station header
            if code:
                lines.append(f"\n{name} (⁠ {code} ⁠)")
            else:
                lines.append(f"\n{name}")

            # Timings
            lines.append(f"{labels['arrival_time']} {arrival} | {labels['departure_time']} {departure}")

            # Platform
            if platform:
                lines.append(f"{labels['platform']}: {platform}")

    # Fetched at
    lines.append(f"\n{labels['fetched_at']} {fetched_at}")

    return "\n".join(lines)


async def handle_pnr_status(state: BotState) -> dict:
    """
    Node function: Check PNR status.

    Args:
        state: Current bot state with PNR number in entities

    Returns:
        Updated state with PNR status or error
    """
    entities = state.get("extracted_entities", {})
    pnr = entities.get("pnr", "")

    # Try to extract PNR from query if not in entities
    if not pnr:
        pnr = extract_pnr(state.get("current_query", ""))

    # Validate PNR format
    if not pnr or len(pnr) != 10 or not pnr.isdigit():
        return {
            "response_text": (
                "*PNR Status*\n\n"
                "Please provide a valid 10-digit PNR number.\n\n"
                "*Example:* PNR 1234567890\n\n"
                "_You can find your PNR on your ticket or booking confirmation._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": PNR_INTENT,
        }

    try:
        settings = get_settings()
        travel_service = get_travel_service(settings.railway_api_key)

        logger.info(f"Checking PNR status for: {pnr}")
        result = await travel_service.get_pnr_status(pnr)

        if result.get("success"):
            data = result.get("data", {})

            # Validate that we have meaningful data
            train_name = data.get('train_name', 'N/A')
            train_number = data.get('train_number', 'N/A')

            # Check if data is essentially empty
            if train_name == 'N/A' and train_number == 'N/A':
                logger.warning(f"PNR {pnr} returned empty data")
                return {
                    "tool_result": result,
                    "response_text": (
                        f"*PNR Status: {pnr}*\n\n"
                        "Could not retrieve PNR details.\n\n"
                        "*Possible reasons:*\n"
                        "- PNR number may be incorrect\n"
                        "- PNR may have expired (60 days old)\n"
                        "- Railway server is not responding\n\n"
                        "_Please verify your PNR and try again._"
                    ),
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": PNR_INTENT,
                }

            # Format PNR status for WhatsApp
            response_lines = [
                f"*PNR Status: {pnr}*\n",
                f"Train: *{train_name}* ({train_number})",
                f"From: {data.get('from_station', 'N/A')}",
                f"To: {data.get('to_station', 'N/A')}",
                f"Date: {data.get('journey_date', 'N/A')}",
                f"Class: {data.get('class', 'N/A')}",
            ]

            # Chart status
            chart_status = "Yes" if data.get("chart_prepared") else "No"
            response_lines.append(f"Chart Prepared: {chart_status}")

            # Passenger status
            passengers = data.get("passengers", [])
            if passengers:
                response_lines.append("\n*Passenger Status:*")
                for i, p in enumerate(passengers, 1):
                    booking = p.get("booking_status", "N/A")
                    current = p.get("current_status", "N/A")
                    coach = p.get("coach", "")
                    berth = p.get("berth", "")

                    status_line = f"{i}. Booking: {booking}"
                    if current and current != booking:
                        status_line += f" → Current: {current}"
                    if coach and berth:
                        status_line += f" ({coach}/{berth})"

                    response_lines.append(status_line)
            else:
                response_lines.append("\n_No passenger details available_")

            logger.info(f"Successfully retrieved PNR status for {pnr}")
            return {
                "tool_result": result,
                "response_text": "\n".join(response_lines),
                "response_type": "text",
                "should_fallback": False,
                "intent": PNR_INTENT,
            }
        else:
            error = result.get("error", "Unable to fetch PNR status")
            logger.warning(f"PNR lookup failed for {pnr}: {error}")
            return {
                "tool_result": result,
                "response_text": (
                    f"*PNR Status: {pnr}*\n\n"
                    "Could not fetch PNR status.\n\n"
                    "*Possible reasons:*\n"
                    "- PNR not found or expired\n"
                    "- Railway server temporarily down\n\n"
                    "_Please verify the PNR and try again._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": PNR_INTENT,
            }

    except Exception as e:
        logger.error(f"PNR status handler error: {e}")
        return {
            "response_text": (
                "*PNR Status*\n\n"
                "An error occurred while checking PNR status.\n\n"
                "_Please try again later._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": PNR_INTENT,
            "error": str(e),
        }


async def handle_train_status(state: BotState) -> dict:
    """
    Node function: Check train running status with detailed emoji format.

    Args:
        state: Current bot state with train number in entities

    Returns:
        Updated state with train status or error
    """
    entities = state.get("extracted_entities", {})
    train_number = entities.get("train_number", "")
    query = state.get("current_query", "")

    # Try to extract train number from query if not in entities
    if not train_number:
        train_number = extract_train_number(query)

    # Detect requested language
    target_lang = detect_requested_language(query, "en")

    # Validate train number format
    if not train_number or not (4 <= len(train_number) <= 5) or not train_number.isdigit():
        if target_lang == "hi":
            return {
                "response_text": (
                    "कृपया ट्रेन नंबर प्रदान करें।\n"
                    "उदाहरण: ट्रेन 12301 की स्थिति"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": TRAIN_INTENT,
            }
        elif target_lang == "kn":
            return {
                "response_text": (
                    "ದಯವಿಟ್ಟು ರೈಲು ಸಂಖ್ಯೆಯನ್ನು ನೀಡಿ.\n"
                    "ಉದಾಹರಣೆ: ರೈಲು 12301 ಸ್ಥಿತಿ"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": TRAIN_INTENT,
            }
        elif target_lang == "ta":
            return {
                "response_text": (
                    "தயவுசெய்து ரயில் எண்ணை வழங்கவும்.\n"
                    "எடுத்துக்காட்டு: ரயில் 12301 நிலை"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": TRAIN_INTENT,
            }
        elif target_lang == "te":
            return {
                "response_text": (
                    "దయచేసి రైలు నంబర్ అందించండి.\n"
                    "ఉదాహరణ: రైలు 12301 స్థితి"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": TRAIN_INTENT,
            }
        return {
            "response_text": (
                "*Train Status*\n\n"
                "Please provide a valid train number (4-5 digits).\n\n"
                "*Example:* Train 12301 status\n\n"
                "_You can find your train number on your ticket._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": TRAIN_INTENT,
        }

    data = None
    error_msg = None

    # Try RapidAPI first
    try:
        settings = get_settings()
        travel_service = get_travel_service(settings.railway_api_key)

        logger.info(f"Checking train status for: {train_number}")
        result = await travel_service.get_train_status(train_number)

        if result.get("success"):
            data = result.get("data", {})
            # Check if it's demo data (no meaningful info)
            if data.get("train_name", "").startswith("Express") or data.get("train_name") == "N/A":
                logger.info("API returned demo data, will try scraper")
                data = None
            else:
                logger.info(f"Train status fetched via API for {train_number}")
        else:
            error_msg = result.get("error", "API error")
            logger.warning(f"API failed for {train_number}: {error_msg}")
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"API exception for {train_number}: {e}")

    # Fallback to web scraping if API failed or returned demo data
    if not data:
        try:
            logger.info(f"Falling back to web scraper for {train_number}")
            scrape_result = await scrape_train_status_detailed(train_number)
            if scrape_result["success"] and scrape_result.get("data"):
                data = scrape_result["data"]
                logger.info(f"Train status fetched via scraper for {train_number}")
            else:
                error_msg = scrape_result.get("error", "Scraping failed")
                logger.warning(f"Scraper failed for {train_number}: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Scraper exception for {train_number}: {e}")

    # Return response
    if data:
        # Use detailed format
        response = format_detailed_train_status(data, target_lang)

        logger.info(f"Successfully retrieved train status for {train_number}")
        return {
            "tool_result": {"success": True, "data": data},
            "response_text": response,
            "response_type": "text",
            "should_fallback": False,
            "intent": TRAIN_INTENT,
        }
    else:
        # Error response in appropriate language
        if target_lang == "hi":
            error_text = (
                f"ट्रेन {train_number} की स्थिति प्राप्त नहीं हो सकी।\n\n"
                "*संभावित कारण:*\n"
                "- आज ट्रेन नहीं चल रही\n"
                "- गलत ट्रेन नंबर\n"
                "- सेवा अस्थायी रूप से अनुपलब्ध\n\n"
                "_कृपया बाद में पुनः प्रयास करें।_"
            )
        elif target_lang == "kn":
            error_text = (
                f"ರೈಲು {train_number} ಸ್ಥಿತಿ ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.\n\n"
                "*ಸಂಭಾವ್ಯ ಕಾರಣಗಳು:*\n"
                "- ಇಂದು ರೈಲು ಓಡುತ್ತಿಲ್ಲ\n"
                "- ತಪ್ಪು ರೈಲು ಸಂಖ್ಯೆ\n"
                "- ಸೇವೆ ತಾತ್ಕಾಲಿಕವಾಗಿ ಲಭ್ಯವಿಲ್ಲ\n\n"
                "_ದಯವಿಟ್ಟು ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ._"
            )
        elif target_lang == "ta":
            error_text = (
                f"ரயில் {train_number} நிலையைப் பெற முடியவில்லை.\n\n"
                "*சாத்தியமான காரணங்கள்:*\n"
                "- இன்று ரயில் இயங்கவில்லை\n"
                "- தவறான ரயில் எண்\n"
                "- சேவை தற்காலிகமாக கிடைக்கவில்லை\n\n"
                "_தயவுசெய்து பின்னர் மீண்டும் முயற்சிக்கவும்._"
            )
        elif target_lang == "te":
            error_text = (
                f"రైలు {train_number} స్థితిని పొందలేకపోయాము.\n\n"
                "*సాధ్యమయ్యే కారణాలు:*\n"
                "- ఈ రోజు రైలు నడవడం లేదు\n"
                "- తప్పు రైలు నంబర్\n"
                "- సేవ తాత్కాలికంగా అందుబాటులో లేదు\n\n"
                "_దయచేసి తర్వాత మళ్ళీ ప్రయత్నించండి._"
            )
        else:
            error_text = (
                f"*Train Status: {train_number}*\n\n"
                "Could not fetch train status.\n\n"
                "*Possible reasons:*\n"
                "- Train number may be incorrect\n"
                "- Train may not be running today\n"
                "- Railway server temporarily down\n\n"
                "_Please verify the train number and try again._"
            )
        return {
            "response_text": error_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": TRAIN_INTENT,
            "error": error_msg,
        }
