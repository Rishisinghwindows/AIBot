"""
Follow-up Question Handler

Intelligent handling of follow-up questions in multi-turn conversations.
Supports:
- Topic continuation ("what about career?" after marriage prediction)
- Clarification requests ("tell me more", "why?", "explain")
- Entity references ("my 7th house", "that dosha")
- Multi-language follow-ups (Hindi, Bengali, Tamil, etc.)

Best Practices Implemented:
1. Context reuse for related questions
2. Graceful fallback when context expires
3. Seamless topic switching detection
4. Multi-language continuation phrases
"""

import re
import logging
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FollowupType(Enum):
    """Types of follow-up questions."""
    TOPIC_CONTINUATION = "topic_continuation"      # "What about career?"
    CLARIFICATION = "clarification"                # "Tell me more", "Why?"
    ELABORATION = "elaboration"                    # "Explain that", "What does it mean?"
    ENTITY_REFERENCE = "entity_reference"          # "My 7th house", "That planet"
    CONFIRMATION = "confirmation"                  # "Yes", "No"
    NEGATION = "negation"                         # "No", "Cancel"
    NEW_TOPIC = "new_topic"                       # Clear topic switch
    UNKNOWN = "unknown"


@dataclass
class FollowupAnalysis:
    """Result of follow-up analysis."""
    followup_type: FollowupType
    should_use_context: bool
    referenced_entity: Optional[str] = None       # e.g., "career", "7th house"
    referenced_topic: Optional[str] = None        # e.g., "life_prediction"
    confidence: float = 0.0
    reason: str = ""


# =============================================================================
# CONTINUATION PHRASES (Multi-language)
# =============================================================================

CONTINUATION_PHRASES = {
    # English
    "en": {
        "topic_continuation": [
            "what about", "how about", "and what about", "also tell",
            "what if", "and", "also", "similarly", "same for",
            "now tell me about", "what's my", "tell me about my",
        ],
        "clarification": [
            "tell me more", "more details", "explain", "elaborate",
            "can you explain", "what do you mean", "i don't understand",
            "be more specific", "give me details", "more info",
        ],
        "elaboration": [
            "why", "how", "what does it mean", "meaning of",
            "reason", "because", "explain why", "how come",
            "what causes", "what leads to",
        ],
        "confirmation": [
            "yes", "yeah", "yep", "sure", "ok", "okay", "correct",
            "right", "proceed", "continue", "go ahead", "yes please",
        ],
        "negation": [
            "no", "nope", "nah", "cancel", "stop", "nevermind",
            "forget it", "don't", "not interested", "skip",
        ],
    },
    # Hindi
    "hi": {
        "topic_continuation": [
            "aur", "aur batao", "aur kya", "iske baare mein",
            "aur bhi", "yeh bhi batao", "iska kya", "ab",
            "career ke baare mein", "shaadi ke baare mein",
        ],
        "clarification": [
            "aur batao", "detail mein", "samjhao", "explain karo",
            "thoda aur", "puri baat batao", "clear karo",
        ],
        "elaboration": [
            "kyun", "kaise", "iska matlab", "matlab kya hai",
            "kya matlab", "wajah", "reason kya hai",
        ],
        "confirmation": [
            "haan", "ha", "ji", "theek hai", "sahi hai", "bilkul",
            "zaroor", "ok", "aage batao", "continue",
        ],
        "negation": [
            "nahi", "na", "mat", "band karo", "chhodo", "rehne do",
            "nahi chahiye", "cancel", "rok do",
        ],
    },
    # Bengali
    "bn": {
        "topic_continuation": [
            "ar", "ar ki", "ebaro", "eta ki", "ar bolo",
        ],
        "clarification": [
            "ar bolo", "bistarito", "bujhiye bolo",
        ],
        "confirmation": [
            "hyan", "ha", "thik ache", "hobe",
        ],
        "negation": [
            "na", "noi", "korbo na", "thak",
        ],
    },
    # Tamil
    "ta": {
        "topic_continuation": [
            "innum", "athu enna", "ithu pathi",
        ],
        "confirmation": [
            "aam", "seri", "ok", "sariya",
        ],
        "negation": [
            "illa", "vendam", "niruthungal",
        ],
    },
}

# Topics that can continue from each other
RELATED_TOPICS = {
    "life_prediction": ["marriage", "career", "health", "wealth", "children", "foreign"],
    "dosha_check": ["manglik", "kaal_sarp", "sade_sati", "pitra"],
    "birth_chart": ["houses", "planets", "aspects", "dasha", "yogas"],
    "kundli_matching": ["compatibility", "gun_milan", "doshas"],
}

# Entity patterns for reference detection
ENTITY_PATTERNS = {
    "house": r"(\d+)(st|nd|rd|th)?\s*(house|bhav|bhava)",
    "planet": r"(sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu|surya|chandra|mangal|budh|guru|shukra|shani)",
    "sign": r"(aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces|mesh|vrishabh|mithun|kark|singh|kanya|tula|vrishchik|dhanu|makar|kumbh|meen)",
    "prediction_type": r"(marriage|career|health|wealth|children|foreign|shaadi|naukri|dhan|santan|videsh)",
}


# =============================================================================
# FOLLOW-UP ANALYZER
# =============================================================================

class FollowupAnalyzer:
    """
    Analyzes user messages to detect follow-up patterns.

    Usage:
        analyzer = FollowupAnalyzer()
        result = analyzer.analyze("What about my career?", context, lang="en")
        if result.should_use_context:
            # Reuse birth details from context
    """

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self._entity_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in ENTITY_PATTERNS.items()
        }

    def analyze(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> FollowupAnalysis:
        """
        Analyze message for follow-up patterns.

        Args:
            message: User's message
            context: Existing conversation context
            language: Detected language code

        Returns:
            FollowupAnalysis with recommendations
        """
        message_lower = message.lower().strip()

        # Check for topic continuation
        topic_result = self._check_topic_continuation(message_lower, context, language)
        if topic_result:
            return topic_result

        # Check for clarification requests
        clarification_result = self._check_clarification(message_lower, context, language)
        if clarification_result:
            return clarification_result

        # Check for elaboration requests
        elaboration_result = self._check_elaboration(message_lower, context, language)
        if elaboration_result:
            return elaboration_result

        # Check for confirmation/negation
        confirm_result = self._check_confirmation(message_lower, language)
        if confirm_result:
            return confirm_result

        # Check for entity references
        entity_result = self._check_entity_reference(message_lower, context)
        if entity_result:
            return entity_result

        # Default: treat as new topic if context exists but no match
        if context:
            return FollowupAnalysis(
                followup_type=FollowupType.NEW_TOPIC,
                should_use_context=False,
                confidence=0.3,
                reason="no_continuation_pattern_detected"
            )

        return FollowupAnalysis(
            followup_type=FollowupType.UNKNOWN,
            should_use_context=False,
            confidence=0.0,
            reason="no_context_available"
        )

    def _check_topic_continuation(
        self,
        message: str,
        context: Optional[Dict],
        language: str
    ) -> Optional[FollowupAnalysis]:
        """Check if message is continuing a topic."""
        phrases = CONTINUATION_PHRASES.get(language, {}).get("topic_continuation", [])
        phrases.extend(CONTINUATION_PHRASES.get("en", {}).get("topic_continuation", []))

        for phrase in phrases:
            if phrase in message:
                # Extract what they're asking about
                referenced = self._extract_topic_reference(message)

                return FollowupAnalysis(
                    followup_type=FollowupType.TOPIC_CONTINUATION,
                    should_use_context=True,
                    referenced_topic=referenced,
                    confidence=0.85,
                    reason=f"continuation_phrase:{phrase}"
                )

        # Check for prediction type mentions (implicit continuation)
        for pattern_name, pattern in self._entity_patterns.items():
            if pattern_name == "prediction_type":
                match = pattern.search(message)
                if match and context:
                    return FollowupAnalysis(
                        followup_type=FollowupType.TOPIC_CONTINUATION,
                        should_use_context=True,
                        referenced_entity=match.group(1),
                        confidence=0.75,
                        reason=f"implicit_topic_reference:{match.group(1)}"
                    )

        return None

    def _check_clarification(
        self,
        message: str,
        context: Optional[Dict],
        language: str
    ) -> Optional[FollowupAnalysis]:
        """Check if message is asking for clarification."""
        phrases = CONTINUATION_PHRASES.get(language, {}).get("clarification", [])
        phrases.extend(CONTINUATION_PHRASES.get("en", {}).get("clarification", []))

        for phrase in phrases:
            if phrase in message:
                return FollowupAnalysis(
                    followup_type=FollowupType.CLARIFICATION,
                    should_use_context=True,
                    confidence=0.9,
                    reason=f"clarification_phrase:{phrase}"
                )

        return None

    def _check_elaboration(
        self,
        message: str,
        context: Optional[Dict],
        language: str
    ) -> Optional[FollowupAnalysis]:
        """Check if message is asking for elaboration."""
        phrases = CONTINUATION_PHRASES.get(language, {}).get("elaboration", [])
        phrases.extend(CONTINUATION_PHRASES.get("en", {}).get("elaboration", []))

        for phrase in phrases:
            if message.startswith(phrase) or f" {phrase}" in message:
                return FollowupAnalysis(
                    followup_type=FollowupType.ELABORATION,
                    should_use_context=True,
                    confidence=0.85,
                    reason=f"elaboration_phrase:{phrase}"
                )

        return None

    def _check_confirmation(
        self,
        message: str,
        language: str
    ) -> Optional[FollowupAnalysis]:
        """Check if message is confirmation or negation."""
        # Check confirmation
        confirm_phrases = CONTINUATION_PHRASES.get(language, {}).get("confirmation", [])
        confirm_phrases.extend(CONTINUATION_PHRASES.get("en", {}).get("confirmation", []))

        for phrase in confirm_phrases:
            if message == phrase or message.startswith(f"{phrase} "):
                return FollowupAnalysis(
                    followup_type=FollowupType.CONFIRMATION,
                    should_use_context=True,
                    confidence=0.95,
                    reason=f"confirmation:{phrase}"
                )

        # Check negation
        negate_phrases = CONTINUATION_PHRASES.get(language, {}).get("negation", [])
        negate_phrases.extend(CONTINUATION_PHRASES.get("en", {}).get("negation", []))

        for phrase in negate_phrases:
            if message == phrase or message.startswith(f"{phrase} "):
                return FollowupAnalysis(
                    followup_type=FollowupType.NEGATION,
                    should_use_context=True,
                    confidence=0.95,
                    reason=f"negation:{phrase}"
                )

        return None

    def _check_entity_reference(
        self,
        message: str,
        context: Optional[Dict]
    ) -> Optional[FollowupAnalysis]:
        """Check if message references a specific astrological entity."""
        for entity_type, pattern in self._entity_patterns.items():
            match = pattern.search(message)
            if match:
                return FollowupAnalysis(
                    followup_type=FollowupType.ENTITY_REFERENCE,
                    should_use_context=True,
                    referenced_entity=match.group(0),
                    confidence=0.7,
                    reason=f"entity_reference:{entity_type}:{match.group(0)}"
                )

        return None

    def _extract_topic_reference(self, message: str) -> Optional[str]:
        """Extract what topic the user is asking about."""
        # Common patterns
        patterns = [
            r"what about (?:my )?(\w+)",
            r"how about (?:my )?(\w+)",
            r"tell me about (?:my )?(\w+)",
            r"(\w+) ke baare mein",  # Hindi
            r"aur (\w+)",  # Hindi
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)

        return None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def should_reuse_birth_details(
    current_intent: str,
    previous_intent: str,
    context: Dict[str, Any]
) -> bool:
    """
    Determine if birth details should be reused from context.

    Args:
        current_intent: Current detected intent
        previous_intent: Previous intent from context
        context: Existing context with birth details

    Returns:
        True if birth details should be reused
    """
    # Check if we have birth details
    birth_details = ["birth_date", "birth_time", "birth_place"]
    context_data = context.get("data", {})

    has_birth_details = all(
        context_data.get(key) for key in birth_details
    )

    if not has_birth_details:
        return False

    # Intents that benefit from reusing birth details
    reuse_intents = [
        "life_prediction", "dosha_check", "birth_chart",
        "numerology", "dasha", "transit",
    ]

    # Check if current intent can use birth details
    current_base = current_intent.replace("astro_", "")
    previous_base = previous_intent.replace("astro_", "") if previous_intent else ""

    # Same category of prediction - definitely reuse
    if current_base in reuse_intents:
        return True

    # Related topics
    for topic, related in RELATED_TOPICS.items():
        if previous_base == topic or previous_base in related:
            if current_base in related or current_base == topic:
                return True

    return False


def get_followup_prompt(
    followup_type: FollowupType,
    language: str = "en",
    referenced_topic: str = None
) -> str:
    """
    Get appropriate prompt for follow-up handling.

    Args:
        followup_type: Type of follow-up detected
        language: User's language
        referenced_topic: Topic they're asking about

    Returns:
        Prompt to show user
    """
    prompts = {
        "en": {
            FollowupType.TOPIC_CONTINUATION: f"Sure, let me tell you about {referenced_topic or 'that'}...",
            FollowupType.CLARIFICATION: "Let me explain in more detail...",
            FollowupType.ELABORATION: "Here's why...",
            FollowupType.CONFIRMATION: "Great, proceeding...",
            FollowupType.NEGATION: "Okay, let me know if you need anything else.",
        },
        "hi": {
            FollowupType.TOPIC_CONTINUATION: f"ज़रूर, मैं आपको {referenced_topic or 'इसके'} बारे में बताता हूं...",
            FollowupType.CLARIFICATION: "मैं विस्तार से समझाता हूं...",
            FollowupType.ELABORATION: "इसका कारण यह है...",
            FollowupType.CONFIRMATION: "ठीक है, आगे बढ़ते हैं...",
            FollowupType.NEGATION: "ठीक है, कुछ और चाहिए तो बताइए।",
        },
    }

    lang_prompts = prompts.get(language, prompts["en"])
    return lang_prompts.get(followup_type, "")


# =============================================================================
# SINGLETON
# =============================================================================

_followup_analyzer: Optional[FollowupAnalyzer] = None


def get_followup_analyzer() -> FollowupAnalyzer:
    """Get singleton FollowupAnalyzer instance."""
    global _followup_analyzer
    if _followup_analyzer is None:
        _followup_analyzer = FollowupAnalyzer()
    return _followup_analyzer
