"""
WhatsApp Conversation Manager

Handles the unique challenges of WhatsApp bot conversations:
1. Single thread per user (no "new chat" option)
2. Users switch topics freely mid-conversation
3. Context should NOT persist indefinitely
4. Multi-turn flows need temporary context

Key Principles (learned from Puch.ai and best practices):
- STATELESS BY DEFAULT: Each message analyzed fresh
- SELECTIVE CONTEXT: Only for explicit multi-turn flows
- SHORT-LIVED: Context expires after inactivity
- INTENT OVERRIDE: New clear intent = new context

Example Flow:
    User: "Aries horoscope"        → Horoscope (no context needed)
    User: "Weather in Delhi"       → Weather (topic switch, fresh)
    User: "When will I get married?" → Life prediction (asks for DOB)
    User: "15-08-1990 10:30 AM Delhi" → Continues prediction (context used)
    User: "What about career?"     → Career prediction (reuses DOB from context)
    User: "News today"             → News (topic switch, context cleared)

Supports:
- Multi-language conversations (22 Indian languages)
- Step-based flows for data collection
- Lite mode (in-memory only, no database)
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

from bot.stores import get_store
from bot.i18n import detect_language, get_translator
from bot.flows import get_flow_manager

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Possible conversation states."""
    IDLE = "idle"                          # No active context
    AWAITING_BIRTH_DETAILS = "awaiting_birth_details"  # Waiting for DOB/time/place
    AWAITING_SECOND_PERSON = "awaiting_second_person"  # Kundli matching - need 2nd person
    AWAITING_GAME_ANSWER = "awaiting_game_answer"      # Word game in progress
    AWAITING_CONFIRMATION = "awaiting_confirmation"    # Yes/no confirmation


class ConversationManager:
    """
    Manages conversation context for WhatsApp bot.

    Design Philosophy:
    - Most messages are processed WITHOUT context (stateless)
    - Context is only used for explicit multi-turn flows
    - Context auto-expires after inactivity
    - New strong intent clears old context
    """

    # Context expiry times
    CONTEXT_EXPIRY_MINUTES = {
        ConversationState.AWAITING_BIRTH_DETAILS: 5,     # 5 min to provide DOB
        ConversationState.AWAITING_SECOND_PERSON: 5,     # 5 min for 2nd person
        ConversationState.AWAITING_GAME_ANSWER: 10,      # 10 min for game
        ConversationState.AWAITING_CONFIRMATION: 2,      # 2 min for yes/no
    }

    # Strong intents that ALWAYS create new context (override existing)
    STRONG_INTENTS = [
        "get_horoscope", "birth_chart", "kundli_matching",
        "weather", "get_news", "pnr_status", "train_status",
        "image", "local_search", "word_game", "tarot_reading",
    ]

    # Intents that may need context continuation
    CONTEXT_AWARE_INTENTS = [
        "life_prediction", "dosha_check", "numerology",
        "get_panchang", "get_remedy", "find_muhurta",
    ]

    def __init__(self):
        self._contexts: Dict[str, Dict[str, Any]] = {}  # In-memory cache
        self._user_languages: Dict[str, str] = {}  # Cache detected languages

    async def detect_user_language(self, phone: str, message: str) -> str:
        """
        Detect and cache user's language.

        Args:
            phone: User's phone number
            message: User's message text

        Returns:
            Language code (e.g., "hi", "bn", "en")
        """
        # Check cache first
        if phone in self._user_languages:
            return self._user_languages[phone]

        # Check stored preference
        store = get_store()
        stored_lang = await store.get_user_language(phone)
        if stored_lang and stored_lang != "en":
            self._user_languages[phone] = stored_lang
            return stored_lang

        # Detect from message
        detected = detect_language(message)

        # Cache and persist if non-English
        if detected != "en":
            self._user_languages[phone] = detected
            await store.save_user_language(phone, detected)

        return detected

    async def check_active_flow(self, phone: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Check if user is in an active step-based flow.

        Args:
            phone: User's phone number
            message: User's message text

        Returns:
            Flow result if in flow, None otherwise
        """
        flow_manager = get_flow_manager()

        # Check for active flow
        if not await flow_manager.is_in_flow(phone):
            return None

        # Get user's language
        lang = await self.detect_user_language(phone, message)

        # Process input through flow
        result = await flow_manager.process_input(phone, message, lang)

        if result.get("no_active_flow"):
            return None

        return result

    async def start_flow(
        self,
        phone: str,
        flow_name: str,
        initial_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Start a step-based flow for the user.

        Args:
            phone: User's phone number
            flow_name: Name of flow to start
            initial_data: Pre-filled data

        Returns:
            Flow start result with first prompt
        """
        flow_manager = get_flow_manager()
        lang = self._user_languages.get(phone, "en")

        return await flow_manager.start_flow(phone, flow_name, initial_data, lang)

    async def get_context(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Get active context for a user if not expired.

        Args:
            phone: User's phone number

        Returns:
            Context dict if active, None otherwise
        """
        # Check in-memory cache first
        if phone in self._contexts:
            ctx = self._contexts[phone]
            if ctx.get("expires_at") and datetime.now() < ctx["expires_at"]:
                return ctx
            else:
                # Expired, remove it
                del self._contexts[phone]
                return None

        # Check database
        try:
            store = get_store()
            db_ctx = await store.get_context(phone, "conversation")
            if db_ctx:
                # Load into memory cache
                self._contexts[phone] = db_ctx
                return db_ctx
        except Exception as e:
            logger.warning(f"Could not load context from DB: {e}")

        return None

    async def set_context(
        self,
        phone: str,
        state: ConversationState,
        data: Dict[str, Any] = None,
        intent: str = None
    ):
        """
        Set conversation context for a user.

        Args:
            phone: User's phone number
            state: New conversation state
            data: Additional context data
            intent: Intent that created this context
        """
        expiry_minutes = self.CONTEXT_EXPIRY_MINUTES.get(state, 5)
        expires_at = datetime.now() + timedelta(minutes=expiry_minutes)

        ctx = {
            "state": state.value,
            "data": data or {},
            "intent": intent,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
        }

        # Store in memory
        self._contexts[phone] = ctx

        # Persist to DB
        try:
            store = get_store()
            await store.save_context(
                phone=phone,
                context_type="conversation",
                context_data=ctx,
                expires_in_minutes=expiry_minutes
            )
        except Exception as e:
            logger.warning(f"Could not save context to DB: {e}")

    async def clear_context(self, phone: str):
        """
        Clear conversation context for a user.

        Args:
            phone: User's phone number
        """
        if phone in self._contexts:
            del self._contexts[phone]

        try:
            store = get_store()
            await store.clear_context(phone, "conversation")
        except Exception as e:
            logger.warning(f"Could not clear context from DB: {e}")

    def should_use_context(
        self,
        current_intent: str,
        current_query: str,
        existing_context: Optional[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Determine if we should use existing context or start fresh.

        Logic:
        1. Strong intent (weather, news, etc.) → ALWAYS fresh
        2. Context-aware intent with active context → Use context
        3. Looks like continuation (short message, DOB pattern) → Use context
        4. Otherwise → Fresh

        Args:
            current_intent: Detected intent for current message
            current_query: Current user message
            existing_context: Existing context if any

        Returns:
            Tuple of (should_use_context, reason)
        """
        # No context exists
        if not existing_context:
            return False, "no_existing_context"

        # Strong intent always starts fresh
        if current_intent in self.STRONG_INTENTS:
            return False, f"strong_intent:{current_intent}"

        # Check if this looks like a context continuation
        query_lower = current_query.lower().strip()

        # Date patterns (user providing DOB)
        import re
        date_pattern = re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', current_query)
        time_pattern = re.search(r'\d{1,2}[:.]\d{2}\s*(am|pm)?', query_lower)

        if date_pattern or time_pattern:
            # Looks like user is providing birth details
            if existing_context.get("state") == ConversationState.AWAITING_BIRTH_DETAILS.value:
                return True, "birth_details_continuation"

        # Very short message might be continuation
        if len(query_lower) < 50 and existing_context:
            ctx_intent = existing_context.get("intent", "")

            # If current intent is context-aware and matches context intent
            if current_intent in self.CONTEXT_AWARE_INTENTS:
                if ctx_intent.replace("astro_", "") in ["life_prediction", "dosha_check"]:
                    return True, "context_aware_continuation"

        # Explicit continuation phrases
        continuation_phrases = [
            "yes", "no", "ok", "okay", "continue", "proceed",
            "what about", "how about", "and", "also",
        ]
        if any(phrase in query_lower for phrase in continuation_phrases):
            return True, "explicit_continuation"

        # Default: start fresh
        return False, "default_fresh_start"

    async def process_message(
        self,
        phone: str,
        query: str,
        detected_intent: str,
        extracted_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a message with conversation context awareness.

        This is the main entry point for conversation management.

        Args:
            phone: User's phone number
            query: User's message text
            detected_intent: Intent detected by intent classifier
            extracted_entities: Entities extracted from message

        Returns:
            Enriched data including context decisions
        """
        # Get existing context
        existing_context = await self.get_context(phone)

        # Decide whether to use context
        use_context, reason = self.should_use_context(
            current_intent=detected_intent,
            current_query=query,
            existing_context=existing_context
        )

        logger.info(f"Context decision for {phone}: use={use_context}, reason={reason}")

        result = {
            "use_context": use_context,
            "context_reason": reason,
            "existing_context": existing_context if use_context else None,
            "intent": detected_intent,
            "entities": extracted_entities,
        }

        # If using context, merge context data with current entities
        if use_context and existing_context:
            ctx_data = existing_context.get("data", {})

            # Merge birth details from context
            for key in ["birth_date", "birth_time", "birth_place", "name"]:
                if not extracted_entities.get(key) and ctx_data.get(key):
                    extracted_entities[key] = ctx_data[key]

            # Keep the original intent if this is a continuation
            if reason in ["birth_details_continuation", "context_aware_continuation"]:
                result["intent"] = existing_context.get("intent", detected_intent)

            result["entities"] = extracted_entities

        # If starting fresh and there was old context, clear it
        if not use_context and existing_context:
            await self.clear_context(phone)

        return result

    async def start_multi_turn_flow(
        self,
        phone: str,
        flow_type: str,
        initial_data: Dict[str, Any] = None
    ):
        """
        Start a multi-turn conversation flow.

        Called when a handler needs more information from user.

        Args:
            phone: User's phone number
            flow_type: Type of flow (birth_details, kundli_matching, etc.)
            initial_data: Data collected so far
        """
        state_map = {
            "birth_details": ConversationState.AWAITING_BIRTH_DETAILS,
            "second_person": ConversationState.AWAITING_SECOND_PERSON,
            "game_answer": ConversationState.AWAITING_GAME_ANSWER,
            "confirmation": ConversationState.AWAITING_CONFIRMATION,
        }

        state = state_map.get(flow_type, ConversationState.IDLE)
        await self.set_context(phone, state, initial_data, flow_type)

    async def complete_flow(self, phone: str):
        """
        Complete a multi-turn flow.

        Args:
            phone: User's phone number
        """
        await self.clear_context(phone)


# Singleton instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get the singleton ConversationManager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

async def enrich_with_context(state: dict) -> dict:
    """
    Enrich state with conversation context, language, and flow state.

    Call this AFTER intent detection but BEFORE routing.

    Args:
        state: Current bot state

    Returns:
        Enriched state with:
        - detected_language: User's detected language
        - conversation_context: Context decisions
        - flow_state: Active flow info if any
    """
    phone = state.get("whatsapp_message", {}).get("from_number", "")
    query = state.get("current_query", "")
    intent = state.get("intent", "chat")
    entities = state.get("extracted_entities", {})

    if not phone:
        return state

    manager = get_conversation_manager()

    # Detect user's language
    lang = await manager.detect_user_language(phone, query)
    state["detected_language"] = lang

    # Check if user is in an active step-based flow
    flow_result = await manager.check_active_flow(phone, query)
    if flow_result:
        state["flow_state"] = flow_result
        # If flow is complete, merge collected data into entities
        if flow_result.get("completed"):
            state["extracted_entities"] = {
                **entities,
                **flow_result.get("collected_data", {})
            }
            # Set intent to the flow's on_complete action
            if flow_result.get("on_complete"):
                state["intent"] = flow_result["on_complete"]
        return state

    # Process message with context manager
    result = await manager.process_message(
        phone=phone,
        query=query,
        detected_intent=intent,
        extracted_entities=entities
    )

    # Update state with enriched data
    state["intent"] = result["intent"]
    state["extracted_entities"] = result["entities"]
    state["conversation_context"] = {
        "use_context": result["use_context"],
        "reason": result["context_reason"],
    }

    return state


async def request_birth_details(phone: str, intent: str, partial_data: dict = None) -> Dict[str, Any]:
    """
    Request birth details from user using step-based flow.

    Args:
        phone: User's phone number
        intent: Original intent (to resume after getting details)
        partial_data: Any birth details already collected

    Returns:
        Flow start result with first prompt
    """
    manager = get_conversation_manager()

    # Use the new flow system
    initial_data = {
        "original_intent": intent,
        **(partial_data or {})
    }

    result = await manager.start_flow(phone, "birth_details", initial_data)

    # Also set legacy context for backward compatibility
    if result.get("started"):
        await manager.start_multi_turn_flow(
            phone=phone,
            flow_type="birth_details",
            initial_data=initial_data
        )

    return result


async def start_life_prediction_flow(phone: str, prediction_type: str = None) -> Dict[str, Any]:
    """
    Start life prediction flow.

    Args:
        phone: User's phone number
        prediction_type: Pre-selected prediction type (marriage, career, etc.)

    Returns:
        Flow start result
    """
    manager = get_conversation_manager()

    initial_data = {}
    if prediction_type:
        initial_data["prediction_type"] = prediction_type

    return await manager.start_flow(phone, "life_prediction", initial_data)


async def start_kundli_matching_flow(phone: str) -> Dict[str, Any]:
    """
    Start kundli matching flow.

    Args:
        phone: User's phone number

    Returns:
        Flow start result
    """
    manager = get_conversation_manager()
    return await manager.start_flow(phone, "kundli_matching")


def get_user_language(phone: str) -> str:
    """
    Get cached user language (sync version).

    Args:
        phone: User's phone number

    Returns:
        Language code or "en"
    """
    manager = get_conversation_manager()
    return manager._user_languages.get(phone, "en")
