"""
Train Journey Planner Node

Fetches train options between two cities on a given date using web search.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Tuple

import httpx

from whatsapp_bot.state import BotState
from whatsapp_bot.config import settings
from common.tools.serper_search import search_google

try:
    from common.services.ai_language_service import ai_translate_response
    AI_TRANSLATE_AVAILABLE = True
except ImportError:
    AI_TRANSLATE_AVAILABLE = False

logger = logging.getLogger(__name__)

INTENT = "train_journey"
ERAIL_CLASS_CODES = [
    "1A", "2A", "3A", "CC", "FC", "SL", "2S", "3E", "GN", "EA", "EC", "EV", "VC", "VS"
]


def _extract_route(query: str) -> Tuple[str, str]:
    if not query:
        return "", ""
    query_lower = query.lower()
    match = re.search(r"from\s+(.+?)\s+to\s+(.+?)(?:\s+on|\s*$)", query_lower)
    if match:
        return match.group(1).strip().title(), match.group(2).strip().title()
    match = re.search(r"(.+?)\s+se\s+(.+?)\s+t(?:ak|k)\b", query_lower)
    if match:
        return match.group(1).strip().title(), match.group(2).strip().title()
    return "", ""


def _extract_date(query: str) -> str:
    if not query:
        return ""
    match = re.search(r"\b(\d{1,2}\s+[a-zA-Z]+)\b", query)
    if match:
        return match.group(1)
    match = re.search(r"\b(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b", query)
    if match:
        return match.group(1)
    return ""


def _extract_trains(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    trains = []
    for item in results:
        text = " ".join(filter(None, [item.get("title", ""), item.get("snippet", "")])).strip()
        if not text:
            continue
        match = re.search(r"\b(\d{4,5})\b", text)
        if not match:
            continue
        train_no = match.group(1)
        name = text.replace(train_no, "").strip(" -–|:•")
        classes = _extract_classes(text)
        fare = _extract_fare(text)
        trains.append({
            "number": train_no,
            "name": name[:80],
            "classes": classes,
            "fare": fare,
        })
        if len(trains) >= 6:
            break
    return trains


def _extract_classes(text: str) -> str:
    if not text:
        return ""
    tokens = re.findall(r"\b(1A|2A|3A|3E|SL|CC|EC|FC|2S|GN|AC)\b", text.upper())
    seen = []
    for token in tokens:
        if token not in seen:
            seen.append(token)
    return ", ".join(seen)


def _extract_fare(text: str) -> str:
    if not text:
        return ""
    match = re.search(
        r"(₹\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:[-–]|to)\s*₹?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).replace("  ", " ").replace("to", "-")
    match = re.search(r"(₹\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?)", text)
    if match:
        return match.group(1)
    match = re.search(r"\bRs\.?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?", text, flags=re.IGNORECASE)
    if match:
        return match.group(0).replace("Rs.", "₹").replace("Rs", "₹")
    return ""


def _extract_erail_station_codes(results: List[Dict[str, str]]) -> Tuple[str, str]:
    for item in results:
        link = item.get("link") or ""
        match = re.search(
            r"erail\.in/(?:hi/)?trains-between-stations/[^/]+-([A-Z]{2,5})/[^/]+-([A-Z]{2,5})",
            link,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1).upper(), match.group(2).upper()
    return "", ""


def _format_run_days(mask: str) -> str:
    if not mask or len(mask) < 7:
        return ""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    active = [day for idx, day in enumerate(days) if idx < len(mask) and mask[idx] == "1"]
    if len(active) == 7:
        return "Daily"
    return " ".join(active)


def _classes_from_mask(mask: str) -> str:
    if not mask:
        return ""
    trimmed = mask[: len(ERAIL_CLASS_CODES)]
    classes = [
        ERAIL_CLASS_CODES[idx]
        for idx, char in enumerate(trimmed)
        if char == "1" and idx < len(ERAIL_CLASS_CODES)
    ]
    return ", ".join(classes)


def _fare_range_from_erail(fare_str: str, class_mask: str) -> str:
    if not fare_str:
        return ""
    parts = fare_str.split(":")
    if len(parts) < 3:
        return ""
    fares = []
    mask = class_mask or ""
    for idx in range(min(len(ERAIL_CLASS_CODES), len(mask))):
        if mask[idx] != "1":
            continue
        fare_index = idx + 2
        if fare_index >= len(parts):
            continue
        entry = parts[fare_index]
        if not entry:
            continue
        values = entry.split(",")
        if not values or not values[0].isdigit():
            continue
        amount = int(values[0])
        if amount > 0:
            fares.append(amount)
    if not fares:
        return ""
    low = min(fares)
    high = max(fares)
    if low == high:
        return f"₹{low:,}"
    return f"₹{low:,} - ₹{high:,} (approx)"


def _parse_erail_trains(raw: str, limit: int = 6) -> List[Dict[str, str]]:
    if not raw or "^" not in raw:
        return []
    trains = []
    parts = raw.split("^")
    for part in parts[1:]:
        fields = part.split("~")
        if len(fields) < 52:
            continue
        train_no = fields[0].strip()
        if not train_no:
            continue
        train = {
            "number": train_no,
            "name": fields[1].strip(),
            "from_name": fields[6].strip(),
            "to_name": fields[8].strip(),
            "depart": fields[10].strip(),
            "arrive": fields[11].strip(),
            "duration": fields[12].strip(),
            "run_days": fields[13].strip(),
            "classes_mask": fields[21].strip(),
            "train_type": fields[50].strip() or fields[32].strip(),
            "train_id": fields[33].strip(),
            "distance_km": fields[39].strip(),
            "fare_str": fields[41].strip(),
            "note": fields[44].strip(),
            "link": f"https://erail.in/train-enquiry/{train_no}",
        }
        trains.append(train)
        if len(trains) >= limit:
            break
    return trains


def _parse_route_stations(raw: str) -> List[str]:
    if not raw:
        return []
    route_section = raw.split("#^")[-1]
    stations = []
    for part in route_section.split("^"):
        fields = part.split("~")
        if len(fields) < 3:
            continue
        name = fields[2].strip()
        if name:
            stations.append(name)
    return stations


async def _fetch_erail_trains(from_code: str, to_code: str) -> str:
    url = (
        "https://erail.in/rail/getTrains.aspx"
        f"?Station_From={from_code}&Station_To={to_code}&DataSource=0&Language=0&Cache=1"
    )
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return ""
        return response.text


async def _fetch_erail_route(train_id: str) -> str:
    if not train_id:
        return ""
    url = (
        "https://erail.in/data.aspx"
        f"?Action=TRAINROUTE&Password=2012&Cache=1&Data1={train_id}&Data2=0"
    )
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return ""
        return response.text


async def handle_train_journey(state: BotState) -> dict:
    """
    Node function: Fetches train options between two cities on a date.
    """
    entities = state.get("extracted_entities", {}) or {}
    detected_lang = state.get("detected_language", "en")
    query = state.get("current_query", "") or state.get("whatsapp_message", {}).get("text", "")

    source = (entities.get("source_city") or "").strip()
    destination = (entities.get("destination_city") or "").strip()
    journey_date = (entities.get("journey_date") or "").strip()

    if not source or not destination:
        src, dst = _extract_route(query)
        source = source or src
        destination = destination or dst
    if not journey_date:
        journey_date = _extract_date(query)

    if not source or not destination:
        prompt = "Please provide source and destination, e.g., 'train from Bengaluru to Delhi on 26 January'."
        return {
            "response_text": prompt,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    date_label = journey_date or datetime.now().strftime("%d %B")
    search_query = (
        f"trains from {source} to {destination} on {date_label} fare classes "
        "site:erail.in OR site:ixigo.com OR site:goibibo.com OR site:confirmtkt.com OR site:indiarailinfo.com"
    )

    try:
        result = await search_google(query=search_query, max_results=8, country="in", locale="en")
        if not result["success"]:
            return {
                "tool_result": result,
                "response_text": "Could not fetch trains right now. Please try again.",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        data = result.get("data", {}) or {}
        results = data.get("results", [])
        trains = []
        from_code, to_code = _extract_erail_station_codes(results)
        if from_code and to_code:
            try:
                raw = await _fetch_erail_trains(from_code, to_code)
                trains = _parse_erail_trains(raw)
            except Exception as e:
                logger.warning(f"Erail fetch failed: {e}")
        if not trains:
            trains = _extract_trains(results)

        lines = [
            f"🚆 *Trains from {source} to {destination}*",
            f"🗓️ Date: {date_label}",
            "",
        ]
        via_added = 0
        if trains:
            for idx, train in enumerate(trains, start=1):
                name = train.get("name") or "Train"
                number = train.get("number") or ""
                lines.append(f"{idx}. {number} - {name}")
                if train.get("depart"):
                    lines.append(f"   • Depart: {train.get('depart')} ({train.get('from_name') or source})")
                if train.get("arrive"):
                    lines.append(f"   • Arrive: {train.get('arrive')} ({train.get('to_name') or destination})")
                duration = train.get("duration") or ""
                if duration:
                    if "hr" not in duration:
                        duration = f"{duration} hr"
                    lines.append(f"   • Duration: {duration}")
                distance = train.get("distance_km") or ""
                if distance:
                    if "km" not in distance:
                        distance = f"{distance} km"
                    lines.append(f"   • Distance: {distance}")
                run_days = _format_run_days(train.get("run_days") or "")
                if run_days:
                    lines.append(f"   • Runs: {run_days}")
                train_type = train.get("train_type") or ""
                if train_type:
                    lines.append(f"   • Type: {train_type}")
                classes = train.get("classes") or _classes_from_mask(train.get("classes_mask") or "")
                if classes:
                    lines.append(f"   • Classes: {classes}")
                fare = train.get("fare") or _fare_range_from_erail(
                    train.get("fare_str") or "",
                    train.get("classes_mask") or "",
                )
                if fare:
                    lines.append(f"   • Fare: {fare}")
                if train.get("note"):
                    lines.append(f"   • Note: {train.get('note')}")
                if from_code and to_code and idx <= 3 and train.get("train_id"):
                    try:
                        route_raw = await _fetch_erail_route(train["train_id"])
                        stations = _parse_route_stations(route_raw)
                        if len(stations) > 2:
                            via = ", ".join(stations[1:5])
                            lines.append(f"   • Via: {via}")
                            via_added += 1
                    except Exception as e:
                        logger.warning(f"Erail route fetch failed: {e}")
                link = train.get("link")
                if link:
                    lines.append(f"   • Link: {link}")
        else:
            lines.append("No train details found. Try another date or check IRCTC.")

        if results:
            lines.append("")
            lines.append("Sources:")
            for idx, item in enumerate(results[:3], start=1):
                link = item.get("link") or ""
                if link:
                    lines.append(f"{idx}) {link}")
        if from_code and to_code and trains and via_added == 0:
            lines.append("")
            lines.append("Note: Route details are not available right now.")

        response_text = "\n".join(lines)
        if detected_lang != "en" and AI_TRANSLATE_AVAILABLE:
            try:
                response_text = await ai_translate_response(
                    text=response_text,
                    target_language=detected_lang,
                    openai_api_key=settings.openai_api_key,
                )
            except Exception as e:
                logger.warning(f"AI translation failed for train journey: {e}")

        return {
            "tool_result": result,
            "response_text": response_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Train journey handler error: {e}")
        return {
            "response_text": "Could not fetch trains right now.",
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }
