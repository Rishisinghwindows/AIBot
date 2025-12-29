"""
Tests for Domain Classifier

Tests the domain classification logic that routes messages to appropriate handlers.
"""

import pytest
from bot.graphs.domain_classifier import classify_domain, DomainType


class TestDomainClassifier:
    """Test domain classification."""

    @pytest.mark.parametrize("query,expected_domain", [
        # Astrology queries
        ("aries horoscope", "astrology"),
        ("my kundli", "astrology"),
        ("birth chart", "astrology"),
        ("mangal dosha", "astrology"),
        ("kaal sarp dosh", "astrology"),
        ("today panchang", "astrology"),
        ("match kundli", "astrology"),
        ("numerology", "astrology"),
        ("tarot reading", "astrology"),
        ("life prediction", "astrology"),
        ("shani sade sati", "astrology"),
        ("rahu ketu transit", "astrology"),

        # Travel queries
        ("pnr 1234567890", "travel"),
        ("check pnr status", "travel"),
        ("train 12301", "travel"),
        ("running status", "travel"),
        ("metro route", "travel"),
        ("delhi metro", "travel"),

        # Utility queries
        ("weather mumbai", "utility"),
        ("temperature today", "utility"),
        ("latest news", "utility"),
        ("headlines", "utility"),
        ("remind me", "utility"),
        ("set reminder", "utility"),
        ("generate image", "utility"),
        ("create picture", "utility"),
        ("restaurants near me", "utility"),
        ("find nearby", "utility"),

        # Game queries
        ("play game", "game"),
        ("word game", "game"),
        ("lets play", "game"),

        # Conversation (fallback)
        ("hello", "conversation"),
        ("how are you", "conversation"),
        ("thank you", "conversation"),
        ("what can you do", "conversation"),
    ])
    def test_domain_classification(self, query: str, expected_domain: str):
        """Test that queries are classified to correct domains."""
        state = {"current_query": query}
        result = classify_domain(state)

        assert "domain" in result
        assert result["domain"] == expected_domain, \
            f"Query '{query}' classified as '{result['domain']}', expected '{expected_domain}'"

    def test_empty_query_defaults_to_conversation(self):
        """Test empty query defaults to conversation domain."""
        state = {"current_query": ""}
        result = classify_domain(state)
        assert result["domain"] == "conversation"

    def test_case_insensitive_classification(self):
        """Test classification is case insensitive."""
        queries = [
            "ARIES HOROSCOPE",
            "Aries Horoscope",
            "aries horoscope",
            "ArIeS HoRoScOpE",
        ]

        for query in queries:
            state = {"current_query": query}
            result = classify_domain(state)
            assert result["domain"] == "astrology", \
                f"Query '{query}' should be classified as astrology"

    def test_mixed_domain_keywords(self):
        """Test queries with keywords from multiple domains."""
        # Primary keyword should win
        state = {"current_query": "horoscope weather today"}
        result = classify_domain(state)
        # Should match first domain found
        assert result["domain"] in ["astrology", "utility"]

    def test_domain_type_enum(self):
        """Test DomainType enum values."""
        assert DomainType.ASTROLOGY == "astrology"
        assert DomainType.TRAVEL == "travel"
        assert DomainType.UTILITY == "utility"
        assert DomainType.GAME == "game"
        assert DomainType.CONVERSATION == "conversation"
