"""
Fact Check Tool

Verifies claims using multiple sources:
1. Google Fact Check Tools API (free)
2. Web search for fact-checking articles
3. AI-based analysis using OpenAI
"""

import httpx
import logging
import re
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI

from bot.config import settings
from bot.state import ToolResult

logger = logging.getLogger(__name__)

# Google Fact Check Tools API (free, no API key required)
GOOGLE_FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


async def search_fact_checks(claim: str, language: str = "en") -> List[Dict[str, Any]]:
    """
    Search Google Fact Check Tools API for existing fact checks.

    Args:
        claim: The claim to search for
        language: Language code (default: en)

    Returns:
        List of fact check results
    """
    try:
        params = {
            "query": claim,
            "languageCode": language,
        }

        # Add API key if available (increases quota)
        if settings.SERPER_API_KEY:
            params["key"] = settings.SERPER_API_KEY

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(GOOGLE_FACT_CHECK_URL, params=params)

            if response.status_code == 200:
                data = response.json()
                claims = data.get("claims", [])

                results = []
                for claim_data in claims[:5]:  # Limit to 5 results
                    claim_review = claim_data.get("claimReview", [{}])[0]
                    results.append({
                        "claim": claim_data.get("text", ""),
                        "claimant": claim_data.get("claimant", "Unknown"),
                        "rating": claim_review.get("textualRating", "Unknown"),
                        "publisher": claim_review.get("publisher", {}).get("name", "Unknown"),
                        "url": claim_review.get("url", ""),
                        "title": claim_review.get("title", ""),
                    })

                return results
            else:
                logger.warning(f"Google Fact Check API returned {response.status_code}")
                return []

    except Exception as e:
        logger.error(f"Google Fact Check API error: {e}")
        return []


async def search_web_for_fact_check(claim: str) -> List[Dict[str, Any]]:
    """
    Search web for fact-checking articles using Serper.

    Args:
        claim: The claim to verify

    Returns:
        List of relevant articles
    """
    if not settings.SERPER_API_KEY:
        return []

    try:
        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json",
        }

        # Search for fact checks about the claim
        search_query = f"fact check {claim}"

        payload = {
            "q": search_query,
            "gl": "in",
            "num": 5,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers=headers,
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get("organic", [])[:5]:
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "url": item.get("link", ""),
                        "source": item.get("source", ""),
                    })

                return results

    except Exception as e:
        logger.error(f"Serper search error: {e}")

    return []


async def analyze_claim_with_ai(
    claim: str,
    fact_check_results: List[Dict],
    web_results: List[Dict],
) -> Dict[str, Any]:
    """
    Use AI to analyze the claim based on gathered evidence.

    Args:
        claim: The claim to analyze
        fact_check_results: Results from fact-checking databases
        web_results: Results from web search

    Returns:
        AI analysis with verdict and explanation
    """
    if not settings.OPENAI_API_KEY:
        return {
            "verdict": "unknown",
            "confidence": 0,
            "explanation": "AI analysis not available",
        }

    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Build context from evidence
        evidence_text = ""

        if fact_check_results:
            evidence_text += "Fact Check Database Results:\n"
            for fc in fact_check_results:
                evidence_text += f"- Claim: {fc['claim']}\n"
                evidence_text += f"  Rating: {fc['rating']} (by {fc['publisher']})\n"

        if web_results:
            evidence_text += "\nWeb Search Results:\n"
            for web in web_results:
                evidence_text += f"- {web['title']}\n"
                evidence_text += f"  {web['snippet']}\n"

        if not evidence_text:
            evidence_text = "No external evidence found."

        prompt = f"""You are a fact-checker. Analyze this claim and provide a verdict.

CLAIM TO VERIFY:
"{claim}"

EVIDENCE GATHERED:
{evidence_text}

Based on the evidence (or lack thereof), provide:
1. VERDICT: One of [TRUE, FALSE, PARTIALLY_TRUE, MISLEADING, UNVERIFIED]
2. CONFIDENCE: A percentage (0-100) of how confident you are
3. EXPLANATION: A brief explanation in 2-3 sentences
4. SOURCES: Key sources used (if any)

Respond in this exact JSON format:
{{
    "verdict": "TRUE|FALSE|PARTIALLY_TRUE|MISLEADING|UNVERIFIED",
    "confidence": 85,
    "explanation": "Brief explanation here",
    "sources": ["source1", "source2"]
}}

Be objective and cautious. If evidence is insufficient, say UNVERIFIED."""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional fact-checker. Be objective, accurate, and cite sources when available."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON response
        import json
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {
                "verdict": "UNVERIFIED",
                "confidence": 50,
                "explanation": "Could not analyze the claim properly.",
                "sources": [],
            }

    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return {
            "verdict": "UNVERIFIED",
            "confidence": 0,
            "explanation": f"Analysis error: {str(e)}",
            "sources": [],
        }


def extract_claim_from_query(query: str) -> str:
    """
    Extract the actual claim from the user's query.

    Args:
        query: User's message

    Returns:
        Extracted claim text
    """
    # Remove common fact-check trigger phrases
    patterns_to_remove = [
        r"^(fact\s*check|check\s*fact|verify|is\s*this\s*(true|real|fake|correct))\s*:?\s*",
        r"^(kya\s*yeh\s*(sach|real|fake)\s*(hai)?)\s*:?\s*",
        r"^(yeh\s*(sach|real|fake)\s*hai\s*kya)\s*:?\s*",
        r"^(please\s*)?(can\s*you\s*)?(verify|check)\s*(this|if)\s*:?\s*",
        r"\?+$",  # Remove trailing question marks
    ]

    claim = query.strip()
    for pattern in patterns_to_remove:
        claim = re.sub(pattern, "", claim, flags=re.IGNORECASE).strip()

    return claim if claim else query


async def fact_check(query: str, language: str = "en") -> ToolResult:
    """
    Main fact-check function that orchestrates the verification process.

    Args:
        query: User's query containing the claim
        language: Language code for results

    Returns:
        ToolResult with fact-check analysis
    """
    try:
        # Extract the actual claim
        claim = extract_claim_from_query(query)

        if not claim or len(claim) < 10:
            return ToolResult(
                success=False,
                data=None,
                error="Please provide a specific claim to verify. Example: 'Fact check: Earth is flat'",
                tool_name="fact_check",
            )

        logger.info(f"Fact checking claim: {claim}")

        # Gather evidence from multiple sources in parallel
        import asyncio

        fact_check_task = search_fact_checks(claim, language)
        web_search_task = search_web_for_fact_check(claim)

        fact_check_results, web_results = await asyncio.gather(
            fact_check_task,
            web_search_task,
        )

        # Analyze with AI
        ai_analysis = await analyze_claim_with_ai(claim, fact_check_results, web_results)

        # Determine if we found existing fact checks
        has_official_fact_check = len(fact_check_results) > 0

        # Build response data
        result_data = {
            "claim": claim,
            "verdict": ai_analysis.get("verdict", "UNVERIFIED"),
            "confidence": ai_analysis.get("confidence", 0),
            "explanation": ai_analysis.get("explanation", ""),
            "has_official_fact_check": has_official_fact_check,
            "fact_check_results": fact_check_results[:3],  # Top 3
            "web_results": web_results[:3],  # Top 3
            "sources": ai_analysis.get("sources", []),
        }

        return ToolResult(
            success=True,
            data=result_data,
            error=None,
            tool_name="fact_check",
        )

    except Exception as e:
        logger.error(f"Fact check failed: {e}")
        return ToolResult(
            success=False,
            data=None,
            error=f"Fact check failed: {str(e)}",
            tool_name="fact_check",
        )


# Verdict emoji mapping
VERDICT_EMOJI = {
    "TRUE": "✅",
    "FALSE": "❌",
    "PARTIALLY_TRUE": "⚠️",
    "MISLEADING": "🟡",
    "UNVERIFIED": "❓",
}

VERDICT_LABELS = {
    "TRUE": {"en": "True", "hi": "सच"},
    "FALSE": {"en": "False", "hi": "झूठ"},
    "PARTIALLY_TRUE": {"en": "Partially True", "hi": "आंशिक सच"},
    "MISLEADING": {"en": "Misleading", "hi": "भ्रामक"},
    "UNVERIFIED": {"en": "Unverified", "hi": "असत्यापित"},
}
