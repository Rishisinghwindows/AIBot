"""
Graph Nodes Package

Contains all LangGraph node functions for processing messages.
"""

from ohgrt_api.graph.nodes.intent import detect_intent
from ohgrt_api.graph.nodes.chat import handle_chat, handle_fallback
from ohgrt_api.graph.nodes.weather_node import handle_weather
from ohgrt_api.graph.nodes.news_node import handle_news
from ohgrt_api.graph.nodes.travel_node import handle_pnr_status, handle_train_status
from ohgrt_api.graph.nodes.image_node import handle_image_generation
from ohgrt_api.graph.nodes.astro_node import (
    handle_horoscope,
    handle_birth_chart,
    handle_numerology,
    handle_tarot,
    handle_panchang,
    handle_dosha,
    handle_kundli_matching,
    handle_life_prediction,
    handle_ask_astrologer,
)

__all__ = [
    # Core nodes
    "detect_intent",
    "handle_chat",
    "handle_fallback",
    # Feature nodes
    "handle_weather",
    "handle_news",
    "handle_pnr_status",
    "handle_train_status",
    "handle_image_generation",
    # Astrology nodes
    "handle_horoscope",
    "handle_birth_chart",
    "handle_numerology",
    "handle_tarot",
    "handle_panchang",
    "handle_dosha",
    "handle_kundli_matching",
    "handle_life_prediction",
    "handle_ask_astrologer",
]
