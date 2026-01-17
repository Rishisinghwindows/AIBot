"""
LangGraph Node Functions

Each node handles a specific intent or processing step.
"""

from common.graph.nodes.intent import detect_intent
from common.graph.nodes.chat import handle_chat, handle_fallback
from common.graph.nodes.local_search import handle_local_search
from common.graph.nodes.image_gen import handle_image_generation
from common.graph.nodes.pnr_status import handle_pnr_status
from common.graph.nodes.train_status import handle_train_status
from common.graph.nodes.train_journey import handle_train_journey
from common.graph.nodes.metro_ticket import handle_metro_ticket
from common.graph.nodes.cricket_score import handle_cricket_score
from common.graph.nodes.govt_jobs import handle_govt_jobs
from common.graph.nodes.govt_schemes import handle_govt_schemes
from common.graph.nodes.farmer_schemes import handle_farmer_schemes
from common.graph.nodes.free_audio_sources import handle_free_audio_sources
from common.graph.nodes.echallan import handle_echallan

__all__ = [
    "detect_intent",
    "handle_chat",
    "handle_fallback",
    "handle_local_search",
    "handle_image_generation",
    "handle_pnr_status",
    "handle_train_status",
    "handle_train_journey",
    "handle_metro_ticket",
    "handle_cricket_score",
    "handle_govt_jobs",
    "handle_govt_schemes",
    "handle_farmer_schemes",
    "handle_free_audio_sources",
    "handle_echallan",
]
