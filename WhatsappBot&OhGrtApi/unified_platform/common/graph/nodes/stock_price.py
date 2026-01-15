"""
Stock Price Node

Fetches stock price info via web search and formats a concise summary.
"""

import logging
import re
import json
import html as html_lib
from datetime import datetime
from typing import Dict, Tuple

import httpx

from common.graph.state import BotState
from common.tools.serper_search import search_google
from common.utils.response_formatter import sanitize_error

logger = logging.getLogger(__name__)

INTENT = "stock_price"


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _clean_stock_name(value: str) -> str:
    cleaned = re.sub(
        r"\b(stock price|share price|stock|share|price|quote|value|rate|today|current|latest)\b",
        "",
        value or "",
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ?")
    return cleaned


def _coerce_attributes(attributes) -> Dict[str, str]:
    if isinstance(attributes, dict):
        return {str(k): str(v) for k, v in attributes.items()}
    if isinstance(attributes, list):
        result = {}
        for item in attributes:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("title") or ""
            value = item.get("value") or item.get("valueText") or ""
            if name:
                result[str(name)] = str(value)
        return result
    return {}


def _pick_attr(attributes: Dict[str, str], candidates: Tuple[str, ...]) -> str:
    candidates_norm = {_normalize_key(c) for c in candidates}
    for key, value in attributes.items():
        if _normalize_key(key) in candidates_norm:
            return value
    return ""


def _extract_price_and_change(answer: str) -> Tuple[str, str]:
    if not answer:
        return "", ""
    change = ""
    change_match = re.search(r"([+-]\s*\d+(?:\.\d+)?%)", answer)
    if change_match:
        change = change_match.group(1).replace(" ", "")
    price_match = re.search(r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)", answer)
    price = price_match.group(1) if price_match else answer.strip()
    return price, change


def _extract_stock_name(state: BotState) -> str:
    entities = state.get("extracted_entities", {}) or {}
    stock_name = (entities.get("stock_name") or entities.get("stock_query") or "").strip()
    if stock_name:
        return _clean_stock_name(stock_name) or stock_name

    query = state.get("current_query", "").strip() or state.get("whatsapp_message", {}).get("text", "")
    if not query:
        return ""

    cleaned = _clean_stock_name(query)
    return cleaned or query


def _extract_rupee_amount(text: str) -> str:
    if not text:
        return ""
    match = re.search(r"(₹\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*₹)", text)
    return match.group(1).replace(" ", "") if match else ""


def _extract_price_from_text(text: str) -> str:
    if not text:
        return ""
    patterns = [
        r"(?:share price|stock price|price)\s*(?:today|is|at|:)?\s*₹\s*([\d,]+(?:\.\d+)?)",
        r"₹\s*([\d,]+(?:\.\d+)?)\s*(?:share price|stock price)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return f"₹{match.group(1)}"
    return ""


def _extract_stat(text: str, labels: Tuple[str, ...]) -> str:
    if not text:
        return ""
    for label in labels:
        pattern = rf"{label}\s*[:\-]?\s*₹?\s*([\d,]+(?:\.\d+)?)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _iter_results(results: list) -> list:
    preferred_domains = ("groww.in", "moneycontrol.com", "screener.in", "etmoney.com", "nseindia.com")
    preferred = []
    rest = []
    for item in results:
        link = (item.get("link") or "").lower()
        if any(domain in link for domain in preferred_domains):
            preferred.append(item)
        else:
            rest.append(item)
    return preferred + rest


def _extract_from_snippets(results: list) -> Dict[str, str]:
    price = ""
    change = ""
    stats = {}
    for item in _iter_results(results):
        text = " ".join(filter(None, [item.get("title", ""), item.get("snippet", "")])).strip()
        if not text:
            continue

        if "52-week high" not in stats or "52-week low" not in stats:
            hl_match = re.search(
                r"52W\s*H/L\s*[:\-]?\s*₹?\s*([\d,]+(?:\.\d+)?)\s*[/\-]\s*₹?\s*([\d,]+(?:\.\d+)?)",
                text,
                flags=re.IGNORECASE,
            )
            if hl_match:
                stats.setdefault("52-week high", f"₹{hl_match.group(1)}")
                stats.setdefault("52-week low", f"₹{hl_match.group(2)}")

        if not price:
            price = _extract_price_from_text(text)
        if not change:
            change_match = re.search(r"([+-]\s*\d+(?:\.\d+)?%)", text)
            if change_match:
                change = change_match.group(1).replace(" ", "")

        if "52-week high" not in stats:
            value = _extract_stat(text, ("52-week high", "52 week high", "52 Week High"))
            if value:
                stats["52-week high"] = f"₹{value}"
        if "52-week low" not in stats:
            value = _extract_stat(text, ("52-week low", "52 week low", "52 Week Low"))
            if value:
                stats["52-week low"] = f"₹{value}"
        if "Market cap" not in stats:
            cap_match = re.search(r"market cap(?:italization)?\s*[:\-]?\s*₹?\s*([\d,.]+)\s*(cr|crore|bn|billion|mn|million)?", text, re.IGNORECASE)
            if cap_match:
                suffix = (cap_match.group(2) or "").strip()
                stats["Market cap"] = f"₹{cap_match.group(1)}{(' ' + suffix) if suffix else ''}".strip()
        if "P/E ratio (TTM)" not in stats:
            pe_match = re.search(r"\bP/E(?:\s*ratio)?\s*[:\-]?\s*([\d,.]+|N/A|NA|n/a)\b", text, re.IGNORECASE)
            if pe_match:
                stats["P/E ratio (TTM)"] = pe_match.group(1)
        if "P/B ratio" not in stats:
            pb_match = re.search(r"\bP/B(?:\s*ratio)?\s*[:\-]?\s*([\d,.]+|N/A|NA|n/a)\b", text, re.IGNORECASE)
            if pb_match:
                stats["P/B ratio"] = pb_match.group(1)

        if price and change and len(stats) >= 2:
            break

    return {
        "price": price,
        "change": change,
        "stats": stats,
    }


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _format_number(value) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{num:,.2f}".rstrip("0").rstrip(".")


def _extract_from_groww_html(text: str) -> Dict[str, str]:
    match = re.search(r"<script[^>]*id=\"__NEXT_DATA__\"[^>]*>(.*?)</script>", text, re.S)
    if not match:
        return {"price": "", "stats": {}}
    data = json.loads(match.group(1))
    stock = (((data.get("props") or {}).get("pageProps") or {}).get("stockData") or {})
    price_data = (stock.get("priceData") or {}).get("nse") or (stock.get("priceData") or {}).get("bse") or {}
    stats_data = stock.get("stats") or {}

    price = price_data.get("ltp")
    year_high = price_data.get("yearHighPrice")
    year_low = price_data.get("yearLowPrice")
    market_cap = stats_data.get("marketCap")
    pe_ratio = stats_data.get("peRatio")
    pb_ratio = stats_data.get("pbRatio")

    stats = {}
    if year_high is not None:
        stats["52-week high"] = f"₹{_format_number(year_high)}"
    if year_low is not None:
        stats["52-week low"] = f"₹{_format_number(year_low)}"
    if market_cap is not None:
        stats["Market cap"] = f"₹{_format_number(market_cap)} Cr"
    if pe_ratio is not None:
        stats["P/E ratio (TTM)"] = _format_number(pe_ratio)
    if pb_ratio is not None:
        stats["P/B ratio"] = _format_number(pb_ratio)

    return {
        "price": f"₹{_format_number(price)}" if price is not None else "",
        "stats": stats,
    }


def _extract_from_html(text: str) -> Dict[str, str]:
    stats = {}
    price = ""
    cleaned = _strip_html(text)

    if not price:
        price_match = re.search(
            r"(?:Current Price|Stock Price|Share Price)\s*₹?\s*([\d,]+(?:\.\d+)?)",
            cleaned,
            flags=re.IGNORECASE,
        )
        if price_match:
            price = f"₹{price_match.group(1)}"

    if "52-week high" not in stats:
        high = _extract_stat(cleaned, ("52 week high", "52-week high"))
        if high:
            stats["52-week high"] = f"₹{high}"
    if "52-week low" not in stats:
        low = _extract_stat(cleaned, ("52 week low", "52-week low"))
        if low:
            stats["52-week low"] = f"₹{low}"

    if "Market cap" not in stats:
        cap_match = re.search(
            r"market cap(?:italization)?\s*₹?\s*([\d,.]+)\s*(cr|crore|bn|billion|mn|million|lakh)?",
            cleaned,
            flags=re.IGNORECASE,
        )
        if cap_match:
            suffix = (cap_match.group(2) or "").strip()
            stats["Market cap"] = f"₹{cap_match.group(1)}{(' ' + suffix) if suffix else ''}".strip()

    if "P/E ratio (TTM)" not in stats:
        pe_match = re.search(r"\bP/E(?:\s*ratio)?(?:\s*\(TTM\))?\s*([\d,.]+|N/A|NA|n/a)\b", cleaned, re.IGNORECASE)
        if pe_match:
            stats["P/E ratio (TTM)"] = pe_match.group(1)

    if "P/B ratio" not in stats:
        pb_match = re.search(r"\bP/B(?:\s*ratio)?\s*([\d,.]+|N/A|NA|n/a)\b", cleaned, re.IGNORECASE)
        if pb_match:
            stats["P/B ratio"] = pb_match.group(1)

    return {"price": price, "stats": stats}


async def _fetch_source_stats(results: list) -> Dict[str, str]:
    preferred_order = ("groww.in", "moneycontrol.com", "screener.in", "etmoney.com", "nseindia.com")
    links = []
    for item in results:
        link = (item.get("link") or "").strip()
        if not link:
            continue
        links.append(link)

    links.sort(key=lambda url: next((i for i, d in enumerate(preferred_order) if d in url), len(preferred_order)))

    for link in links:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    link,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
            if response.status_code != 200:
                continue
            if "groww.in" in link:
                extracted = _extract_from_groww_html(response.text)
            else:
                extracted = _extract_from_html(response.text)
            if extracted.get("price") or (extracted.get("stats") or {}).get("52-week high"):
                return extracted
        except Exception:
            continue
    return {"price": "", "stats": {}}


def _format_response(
    stock_name: str,
    price: str,
    change: str,
    stats: Dict[str, str],
    sources: list,
) -> str:
    date_str = datetime.now().strftime("%d %B %Y")
    header = f"📈 *{stock_name} stock price*"
    lines = [header]

    if price:
        change_text = f" ({change})" if change else ""
        lines.append(f"Latest ({date_str}): {price}{change_text}")
    else:
        lines.append(f"Latest ({date_str}): Not found")

    if stats:
        lines.append("\nKey stats:")
        for label, value in stats.items():
            if value:
                lines.append(f"• {label}: {value}")

    if sources:
        lines.append("\nSources:")
        for idx, source in enumerate(sources[:3], start=1):
            title = source.get("title") or "Source"
            link = source.get("link") or ""
            if link:
                lines.append(f"{idx}) {title} - {link}")

    lines.append("\npowered by web-search")

    return "\n".join(lines)


async def handle_stock_price(state: BotState) -> dict:
    """
    Node function: Fetches stock price info and formats it for chat.
    """
    stock_name = _extract_stock_name(state)
    if not stock_name:
        prompt = "Which stock should I look up?"
        return {
            "response_text": prompt,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    search_query = f"{stock_name} share price"

    try:
        result = await search_google(query=search_query, max_results=6, country="in", locale="en")
        if not result["success"]:
            error_msg = sanitize_error(result.get("error", ""), "search")
            return {
                "tool_result": result,
                "response_text": error_msg or "Could not fetch stock price right now.",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        data = result.get("data", {}) or {}
        answer = data.get("answer") or ""
        knowledge_graph = data.get("knowledge_graph") or {}
        attributes = _coerce_attributes(knowledge_graph.get("attributes"))

        price = ""
        change = ""
        if answer:
            price, change = _extract_price_and_change(answer)

        if not price:
            price = _pick_attr(attributes, ("Stock price", "Share price", "Price"))

        stats = {
            "52-week high": _pick_attr(attributes, ("52-week high", "52 week high", "52 Week High")),
            "52-week low": _pick_attr(attributes, ("52-week low", "52 week low", "52 Week Low")),
            "Market cap": _pick_attr(attributes, ("Market cap", "Market capitalization")),
            "P/E ratio (TTM)": _pick_attr(attributes, ("P/E ratio", "PE ratio", "P/E")),
            "P/B ratio": _pick_attr(attributes, ("P/B ratio", "PB ratio", "P/B")),
        }
        stats = {k: v for k, v in stats.items() if v}

        if not price or len(stats) < 2:
            snippet_data = _extract_from_snippets(data.get("results", []) or [])
            price = price or snippet_data.get("price", "")
            change = change or snippet_data.get("change", "")
            stats.update({k: v for k, v in (snippet_data.get("stats") or {}).items() if v})

        if "52-week high" not in stats or "52-week low" not in stats:
            stats_query = (
                f"{stock_name} 52 week high low "
                "site:groww.in OR site:moneycontrol.com OR site:screener.in"
            )
            stats_result = await search_google(query=stats_query, max_results=5, country="in", locale="en")
            if stats_result.get("success"):
                stats_data = _extract_from_snippets((stats_result.get("data") or {}).get("results", []) or [])
                stats.update({k: v for k, v in (stats_data.get("stats") or {}).items() if v})

        if not price or "52-week high" not in stats or "52-week low" not in stats:
            fetched = await _fetch_source_stats(data.get("results", []) or [])
            price = price or fetched.get("price", "")
            stats.update({k: v for k, v in (fetched.get("stats") or {}).items() if v})

        response_text = _format_response(
            stock_name=stock_name,
            price=price,
            change=change,
            stats=stats,
            sources=data.get("results", []) or [],
        )

        return {
            "tool_result": result,
            "response_text": response_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Stock price handler error: {e}")
        return {
            "response_text": "Could not fetch stock price right now.",
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }
