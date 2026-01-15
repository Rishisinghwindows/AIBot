"""
Cricket Score Node

Fetches live cricket score updates using web search and formats a concise summary.
"""

import logging
import re
import urllib.parse
from datetime import datetime
from typing import List, Dict

from whatsapp_bot.state import BotState
from common.tools.serper_search import search_google
from common.utils.response_formatter import sanitize_error

logger = logging.getLogger(__name__)

INTENT = "cricket_score"


def _extract_team_scores(text: str) -> List[Dict[str, str]]:
    """Extract team score lines from text."""
    lines = []
    pattern = re.compile(r"([A-Za-z][A-Za-z&\.\s]{2,})\s*[:\-]\s*(\d{1,3}[/-]\d{1,2})(?:\s*\(([^)]+)\))?", re.IGNORECASE)
    for match in pattern.finditer(text):
        team = match.group(1).strip()
        score = match.group(2).strip()
        overs = (match.group(3) or "").strip()
        lines.append({
            "team": team,
            "score": score,
            "overs": overs,
        })
        if len(lines) >= 2:
            break
    return lines


def _extract_matches(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Extract match lines from search snippets."""
    matches: List[Dict[str, str]] = []
    team_pattern = re.compile(r"([A-Za-z][A-Za-z&\.\s]{2,})\s+v(?:s)?\.?\s+([A-Za-z][A-Za-z&\.\s]{2,})", re.IGNORECASE)
    score_pattern = re.compile(r"\b\d{1,3}[/-]\d{1,2}\b")
    overs_pattern = re.compile(r"\b\d{1,2}\.\d+\s*(?:ov|over|overs)\b", re.IGNORECASE)

    for item in results:
        text = " ".join(filter(None, [item.get("title", ""), item.get("snippet", "")])).strip()
        if not text:
            continue

        team_match = team_pattern.search(text)
        scores = score_pattern.findall(text)
        overs = overs_pattern.findall(text)
        team_scores = _extract_team_scores(text)

        if not team_match and not scores:
            continue

        teams = ""
        if team_match:
            team_a = team_match.group(1).strip()
            team_b = team_match.group(2).strip()
            teams = f"{team_a} vs {team_b}"

        score_line = " ".join(scores[:2]).strip()
        if overs:
            score_line = f"{score_line} ({overs[0]})".strip()

        if teams or score_line:
            matches.append({
                "teams": teams,
                "score": score_line,
                "team_scores": team_scores,
                "source_text": text,
            })

        if len(matches) >= 3:
            break

    return matches


def _guess_series_title(text: str) -> str:
    """Best-effort series/tournament title from text."""
    candidates = [
        "ipl", "wpl", "sa20", "big bash", "bbl", "psl", "cpl",
        "t20i", "odi", "test", "ranji", "champions trophy",
    ]
    text_lower = text.lower()
    for key in candidates:
        if key in text_lower:
            return key.upper() if key.islower() else key
    return ""


def _format_source_label(link: str) -> str:
    if "cricbuzz" in link:
        return "Cricbuzz"
    if "cricheroes" in link:
        return "CricHeroes"
    if "espncricinfo" in link:
        return "ESPNcricinfo"
    return "Live scores"


def _fallback_live_links() -> List[Dict[str, str]]:
    return [
        {"title": "CricHeroes", "link": "https://cricheroes.com/live-matches"},
        {"title": "Cricbuzz", "link": "https://www.cricbuzz.com/cricket-match/live-scores"},
        {"title": "ESPNcricinfo", "link": "https://www.espncricinfo.com/cricket/scores"},
    ]


def _format_response(
    matches: List[Dict[str, str]],
    sources: List[Dict[str, str]],
    lang: str,
) -> str:
    """Format the response message in the user's language."""
    date_str = datetime.now().strftime("%d %B %Y")
    if lang == "hi":
        title = f"आज के ताज़ा क्रिकेट स्कोर ({date_str}):"
        source_label = "स्रोत"
        prompt = "क्या किसी खास मैच या टीम का स्कोर चाहिए?"
    else:
        title = f"Latest cricket scores ({date_str}):"
        source_label = "Sources"
        prompt = "Want the score for a specific match or team?"

    lines = [f"🏏 *{title}*"]

    if matches:
        for match in matches:
            teams = match.get("teams") or "Match"
            source_text = match.get("source_text", "")
            series = _guess_series_title(source_text)
            if lang == "hi":
                trophy = f"🏆 {series}" if series else "🏆 लाइव मैच"
                lines.append(f"\n{trophy}")
                lines.append(f"{teams}")
            else:
                trophy = f"🏆 {series}" if series else "🏆 Live match"
                lines.append(f"\n{trophy}")
                lines.append(f"{teams}")

            team_scores = match.get("team_scores") or []
            if team_scores:
                for ts in team_scores:
                    team = ts.get("team") or "Team"
                    score = ts.get("score") or ""
                    overs = ts.get("overs") or ""
                    over_text = f" ({overs})" if overs else ""
                    lines.append(f"• {team}: {score}{over_text}")
            else:
                score = match.get("score")
                if score:
                    lines.append(f"• {score}")

            if lang == "hi":
                lines.append("• मैच अभी जारी है — दोनों टीमों के बीच बराबरी का मुकाबला चल रहा है।")
            else:
                lines.append("• Match is live — looks closely contested.")
            if sources:
                src = sources[0]
                label = _format_source_label(src.get("link", "")) or "Live scores"
                link = src.get("link") or ""
                if link:
                    if lang == "hi":
                        lines.append(f"👉 {label} [ {link} ]")
                    else:
                        lines.append(f"👉 {label} [ {link} ]")
    else:
        if lang == "hi":
            lines.append("\nइस समय स्पष्ट स्कोर नहीं मिला। लाइव स्कोर के लिए नीचे दिए लिंक देखें।")
        else:
            lines.append("\nCouldn’t extract clear scores right now. Use the live links below.")

    if sources:
        lines.append(f"\n{source_label}:")
        for src in sources[:3]:
            title = src.get("title") or "Live scores"
            link = src.get("link") or ""
            if link:
                if lang == "hi":
                    lines.append(f"👉 {title} [ {link} ]")
                else:
                    lines.append(f"👉 {title} [ {link} ]")
    else:
        lines.append(f"\n{source_label}:")
        for src in _fallback_live_links():
            if lang == "hi":
                lines.append(f"👉 {src['title']} [ {src['link']} ]")
            else:
                lines.append(f"👉 {src['title']} [ {src['link']} ]")

    lines.append(f"\n{prompt}")
    return "\n".join(lines)


async def handle_cricket_score(state: BotState) -> dict:
    """
    Node function: Fetches live cricket scores and formats them for WhatsApp.
    """
    user_message = state.get("current_query", "").strip() or state.get("whatsapp_message", {}).get("text", "")
    detected_lang = state.get("detected_language", "en")

    if not user_message:
        user_message = "live cricket score"

    query_lower = user_message.lower()
    if "cricket" not in query_lower:
        base_query = f"cricket score {user_message}"
    else:
        base_query = user_message

    search_query = (
        f"{base_query} live score scorecard "
        "site:cricbuzz.com OR site:cricheroes.com OR site:espncricinfo.com"
    )

    try:
        result = await search_google(query=search_query, max_results=6, country="in", locale="en")
        if not result["success"]:
            error_msg = sanitize_error(result.get("error", ""), "search")
            return {
                "tool_result": result,
                "response_text": error_msg or "Could not fetch cricket scores right now.",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        data = result.get("data", {}) or {}
        results = data.get("results", [])
        matches = _extract_matches(results)

        response_text = _format_response(matches, results, detected_lang)
        return {
            "tool_result": result,
            "response_text": response_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Cricket score handler error: {e}")
        return {
            "response_text": "Could not fetch cricket scores right now.",
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }
