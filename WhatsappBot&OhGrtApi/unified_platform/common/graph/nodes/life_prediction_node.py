"""
Life Prediction Node

LangGraph node that handles life prediction requests.
Predicts marriage, career, children, wealth, foreign, health timings.
"""

import logging
from typing import Dict, Any

from common.graph.state import BotState
from common.tools.life_prediction_tool import get_life_prediction
from common.utils.response_formatter import (
    sanitize_error,
    create_missing_input_response,
    create_service_error_response,
)

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "life_prediction"


async def handle_life_prediction(state: BotState) -> dict:
    """
    Handle life prediction requests.

    Predicts major life events based on birth chart:
    - Marriage timing and spouse characteristics
    - Career path and suitable professions
    - Children timing and number
    - Wealth accumulation potential
    - Foreign travel/settlement chances
    - Health outlook

    Args:
        state: Current bot state with extracted entities

    Returns:
        Updated state dict with response
    """
    entities = state.get("extracted_entities", {})
    prediction_type = entities.get("prediction_type", "general")
    birth_date = entities.get("birth_date", "").strip()
    birth_time = entities.get("birth_time", "").strip()
    birth_place = entities.get("birth_place", "").strip()
    question = entities.get("question", "").strip()

    # Check if we have required birth details
    missing = []
    if not birth_date:
        missing.append("birth date (e.g., 15-08-1990)")
    if not birth_time:
        missing.append("birth time (e.g., 10:30 AM)")
    if not birth_place:
        missing.append("birth place (e.g., Delhi)")

    if missing:
        prediction_name = _get_prediction_display_name(prediction_type)
        example = _get_prediction_example(prediction_type)

        return create_missing_input_response(
            missing_fields=missing,
            intent=INTENT,
            feature_name=prediction_name,
            example=example
        )

    try:
        # Call the life prediction tool
        result = await get_life_prediction(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            prediction_type=prediction_type,
            question=question
        )

        if result["success"]:
            return _format_prediction_response(result["data"], prediction_type)
        else:
            raw_error = result.get("error", "")
            user_message = sanitize_error(raw_error, "prediction")
            return {
                "response_text": (
                    f"*{_get_prediction_display_name(prediction_type)}*\n\n"
                    f"{user_message}\n\n"
                    "_Please check your birth details and try again._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"Life prediction handler error: {e}")
        return create_service_error_response(
            intent=INTENT,
            feature_name=_get_prediction_display_name(prediction_type),
            raw_error=str(e)
        )


def _get_prediction_display_name(pred_type: str) -> str:
    """Get display name for prediction type."""
    names = {
        "marriage": "Marriage Prediction",
        "career": "Career Prediction",
        "children": "Children Prediction",
        "wealth": "Wealth Prediction",
        "foreign": "Foreign Settlement Prediction",
        "health": "Health Prediction",
        "general": "Life Prediction"
    }
    return names.get(pred_type, "Life Prediction")


def _get_prediction_example(pred_type: str) -> str:
    """Get example query for prediction type."""
    examples = {
        "marriage": "\"When will I get married? Born 15-08-1990 at 10:30 AM in Delhi\"",
        "career": "\"Career prediction for 15-08-1990 10:30 AM Delhi\"",
        "children": "\"When will I have children? DOB 15-08-1990 10:30 AM Delhi\"",
        "wealth": "\"Will I become rich? 15-08-1990 10:30 AM Delhi\"",
        "foreign": "\"Will I go abroad? Born 15-08-1990 at 10:30 AM in Delhi\"",
        "health": "\"Health prediction for 15-08-1990 10:30 AM Delhi\"",
        "general": "\"My future prediction - 15-08-1990 10:30 AM Delhi\""
    }
    return examples.get(pred_type, "\"Life prediction for 15-08-1990 10:30 AM Delhi\"")


def _format_prediction_response(data: dict, prediction_type: str) -> dict:
    """Format prediction response for WhatsApp."""
    person = data.get("person", {})
    chart_summary = data.get("chart_summary", {})
    current_dasha = data.get("current_dasha", {})
    prediction = data.get("prediction", {})

    response = f"*{_get_prediction_display_name(prediction_type)}*\n\n"

    # Person info
    if person.get("name"):
        response += f"*Name:* {person['name']}\n"
    response += f"*DOB:* {person.get('birth_date', '')}\n"
    response += f"*Time:* {person.get('birth_time', '')}\n"
    response += f"*Place:* {person.get('birth_place', '')}\n\n"

    # Chart summary
    response += "*Chart Summary:*\n"
    response += f"- Ascendant: {chart_summary.get('ascendant', 'N/A')}\n"
    response += f"- Moon Sign: {chart_summary.get('moon_sign', 'N/A')}\n"
    response += f"- Sun Sign: {chart_summary.get('sun_sign', 'N/A')}\n"
    response += f"- Nakshatra: {chart_summary.get('moon_nakshatra', 'N/A')}\n\n"

    # Current Dasha
    if current_dasha and current_dasha.get("mahadasha"):
        response += "*Current Dasha:*\n"
        response += f"- Mahadasha: {current_dasha['mahadasha']}\n"
        response += f"- Remaining: {current_dasha.get('years_remaining', 'N/A')} years\n"
        response += f"- Ends: {current_dasha.get('end_date', 'N/A')}\n"
        response += f"- Next: {current_dasha.get('next_dasha', 'N/A')} Mahadasha\n\n"

    response += "─" * 30 + "\n"

    # Specific prediction
    if prediction_type == "general":
        # Show brief summary of all areas
        response += "\n*LIFE OVERVIEW*\n\n"

        # Marriage
        marriage = prediction.get("marriage", {})
        response += "*Marriage:* "
        response += marriage.get("timing_indication", "Analysis available")[:100] + "\n\n"

        # Career
        career = prediction.get("career", {})
        response += "*Career:* "
        response += career.get("career_outlook", "Analysis available")[:100] + "\n"
        if career.get("suitable_careers"):
            response += f"Suitable fields: {career['suitable_careers'][0][:50]}...\n\n"

        # Wealth
        wealth = prediction.get("wealth", {})
        response += "*Wealth:* "
        response += wealth.get("wealth_outlook", "Analysis available")[:100] + "\n\n"

        # Health
        health = prediction.get("health", {})
        response += "*Health:* "
        response += health.get("health_outlook", "Analysis available")[:100] + "\n\n"

        response += "_Ask specifically about marriage, career, children, wealth, foreign, or health for detailed analysis._"

    else:
        # Detailed single prediction
        response += f"\n*{prediction_type.upper()} ANALYSIS*\n\n"

        if prediction_type == "marriage":
            response += _format_marriage_prediction(prediction)
        elif prediction_type == "career":
            response += _format_career_prediction(prediction)
        elif prediction_type == "children":
            response += _format_children_prediction(prediction)
        elif prediction_type == "wealth":
            response += _format_wealth_prediction(prediction)
        elif prediction_type == "foreign":
            response += _format_foreign_prediction(prediction)
        elif prediction_type == "health":
            response += _format_health_prediction(prediction)

    response += "\n\n_For more personalized guidance, consult a qualified astrologer._"

    return {
        "tool_result": data,
        "response_text": response,
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }


def _format_marriage_prediction(pred: dict) -> str:
    """Format marriage prediction."""
    response = ""

    # 7th house
    house_7 = pred.get("7th_house_analysis", {})
    response += f"*7th House:* {house_7.get('house_sign', 'N/A')}\n"
    response += f"*7th Lord:* {house_7.get('house_lord', 'N/A')} in house {house_7.get('house_lord_position', {}).get('house', 'N/A')}\n\n"

    # Venus position
    venus = pred.get("venus_position", {})
    response += f"*Venus Position:* {venus.get('sign', 'N/A')} (House {venus.get('house', 'N/A')})\n"
    response += f"*Venus Dignity:* {venus.get('dignity', 'N/A')}\n\n"

    # Factors
    factors = pred.get("marriage_factors", {})
    positive = sum(1 for v in factors.values() if v)
    response += f"*Positive Factors:* {positive}/4\n\n"

    # Timing
    response += f"*Timing Indication:*\n{pred.get('timing_indication', 'N/A')}\n\n"

    # Spouse
    response += f"*Spouse Characteristics:*\n{pred.get('spouse_characteristics', 'N/A')}\n\n"
    response += f"*Spouse Direction:* {pred.get('spouse_direction', 'N/A')}\n\n"

    # Advice
    response += f"*Advice:* {pred.get('advice', '')}"

    return response


def _format_career_prediction(pred: dict) -> str:
    """Format career prediction."""
    response = ""

    # 10th house
    house_10 = pred.get("10th_house_analysis", {})
    response += f"*10th House:* {house_10.get('house_sign', 'N/A')}\n"
    response += f"*10th Lord:* {house_10.get('house_lord', 'N/A')} in house {house_10.get('house_lord_position', {}).get('house', 'N/A')}\n\n"

    # Suitable careers
    careers = pred.get("suitable_careers", [])
    if careers:
        response += "*Suitable Career Fields:*\n"
        for career in careers[:3]:
            response += f"- {career}\n"
        response += "\n"

    # Strong planets
    strong_planets = pred.get("strong_planets_indication", [])
    if strong_planets:
        response += "*Career Indications from Planets:*\n"
        for planet in strong_planets[:2]:
            response += f"- {planet['planet']}: {planet['career_indication'][:50]}\n"
        response += "\n"

    # Outlook
    response += f"*Career Outlook:*\n{pred.get('career_outlook', 'N/A')}\n\n"

    # Advice
    response += f"*Advice:* {pred.get('advice', '')}"

    return response


def _format_children_prediction(pred: dict) -> str:
    """Format children prediction."""
    response = ""

    # 5th house
    house_5 = pred.get("5th_house_analysis", {})
    response += f"*5th House:* {house_5.get('house_sign', 'N/A')}\n"
    response += f"*5th Lord:* {house_5.get('house_lord', 'N/A')} in house {house_5.get('house_lord_position', {}).get('house', 'N/A')}\n\n"

    # Jupiter position
    jupiter = pred.get("jupiter_position", {})
    response += f"*Jupiter (Putra Karaka):* {jupiter.get('sign', 'N/A')} (House {jupiter.get('house', 'N/A')})\n"
    response += f"*Jupiter Dignity:* {jupiter.get('dignity', 'N/A')}\n\n"

    # Factors
    factors = pred.get("children_factors", {})
    positive = sum(1 for v in factors.values() if v)
    response += f"*Positive Factors:* {positive}/4\n\n"

    # Timing and number
    response += f"*Timing Indication:*\n{pred.get('timing_indication', 'N/A')}\n\n"
    response += f"*Number Indication:* {pred.get('number_indication', 'N/A')}\n\n"

    # Blessing
    response += f"*Blessing:* {pred.get('blessing', '')}\n\n"

    # Advice
    response += f"*Advice:* {pred.get('advice', '')}"

    return response


def _format_wealth_prediction(pred: dict) -> str:
    """Format wealth prediction."""
    response = ""

    # 2nd house
    house_2 = pred.get("2nd_house_analysis", {})
    response += f"*2nd House (Wealth):* {house_2.get('house_sign', 'N/A')}\n"

    # 11th house
    house_11 = pred.get("11th_house_analysis", {})
    response += f"*11th House (Gains):* {house_11.get('house_sign', 'N/A')}\n\n"

    # Dhana Yoga
    dhana_yoga = pred.get("dhana_yoga", "")
    response += f"*Wealth Yoga:* {dhana_yoga}\n\n"

    # Factors
    factors = pred.get("wealth_factors", {})
    positive = sum(1 for v in factors.values() if v)
    response += f"*Positive Factors:* {positive}/5\n\n"

    # Outlook
    response += f"*Wealth Outlook:*\n{pred.get('wealth_outlook', 'N/A')}\n\n"
    response += f"*Accumulation Period:*\n{pred.get('accumulation_period', 'N/A')}\n\n"

    # Advice
    response += f"*Advice:* {pred.get('advice', '')}"

    return response


def _format_foreign_prediction(pred: dict) -> str:
    """Format foreign prediction."""
    response = ""

    # 12th house
    house_12 = pred.get("12th_house_analysis", {})
    response += f"*12th House (Foreign):* {house_12.get('house_sign', 'N/A')}\n"

    # 9th house
    house_9 = pred.get("9th_house_analysis", {})
    response += f"*9th House (Travel):* {house_9.get('house_sign', 'N/A')}\n\n"

    # Rahu position
    rahu = pred.get("rahu_position", {})
    response += f"*Rahu Position:* {rahu.get('sign', 'N/A')} (House {rahu.get('house', 'N/A')})\n\n"

    # Foreign indicators
    indicators = pred.get("foreign_indicators", [])
    if indicators:
        response += "*Foreign Indicators:*\n"
        for ind in indicators[:3]:
            response += f"- {ind}\n"
        response += "\n"

    # Factors
    factors = pred.get("foreign_factors", {})
    positive = sum(1 for v in factors.values() if v)
    response += f"*Positive Factors:* {positive}/4\n\n"

    # Outlook
    response += f"*Foreign Outlook:*\n{pred.get('foreign_outlook', 'N/A')}\n\n"
    response += f"*Timing:*\n{pred.get('timing', 'N/A')}\n\n"

    # Advice
    response += f"*Advice:* {pred.get('advice', '')}"

    return response


def _format_health_prediction(pred: dict) -> str:
    """Format health prediction."""
    response = ""

    # Ascendant
    house_1 = pred.get("ascendant_analysis", {})
    response += f"*Ascendant:* {house_1.get('house_sign', 'N/A')}\n\n"

    # Vulnerable areas
    response += f"*Vulnerable Body Areas:* {pred.get('vulnerable_areas', 'N/A')}\n\n"

    # Factors
    factors = pred.get("health_factors", {})
    positive = sum(1 for v in factors.values() if v)
    response += f"*Positive Health Factors:* {positive}/4\n\n"

    # Concerns
    concerns = pred.get("health_concerns", [])
    if concerns:
        response += "*Health Concerns:*\n"
        for concern in concerns[:3]:
            response += f"- {concern}\n"
        response += "\n"

    # Outlook
    response += f"*Health Outlook:*\n{pred.get('health_outlook', 'N/A')}\n\n"

    # Advice
    response += f"*Advice:* {pred.get('advice', '')}"

    return response
