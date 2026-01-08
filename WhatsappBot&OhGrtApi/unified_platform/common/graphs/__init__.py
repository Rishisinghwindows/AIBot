"""
Sub-graphs for domain-specific processing.

Architecture:
- Main graph routes to domain sub-graphs
- Each sub-graph handles its own intent detection and tool execution
- Sub-graphs share common state structure
"""

from common.graphs.astro_graph import create_astro_graph, route_astro_intent
from common.graphs.domain_classifier import classify_domain, DomainType

__all__ = [
    "create_astro_graph",
    "route_astro_intent",
    "classify_domain",
    "DomainType",
]
