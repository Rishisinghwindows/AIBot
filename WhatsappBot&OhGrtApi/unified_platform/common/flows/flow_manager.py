"""
Flow Manager

Orchestrates step-based conversation flows.
Handles starting, processing, and completing flows.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from common.flows.base import (
    FlowDefinition,
    FlowState,
    FlowStep,
    ValidationResult,
    get_validator,
)
from common.stores import get_store

logger = logging.getLogger(__name__)


class FlowManager:
    """
    Manages conversation flows for users.

    Usage:
        manager = get_flow_manager()

        # Check for active flow
        state = await manager.get_active_flow(phone)

        # Start new flow
        result = await manager.start_flow(phone, "life_prediction")
        # result = {"prompt": "What's your birth date?", ...}

        # Process user input
        result = await manager.process_input(phone, "15-08-1990")
        # result = {"completed": False, "prompt": "Birth time?"} or
        # result = {"completed": True, "collected_data": {...}}
    """

    def __init__(self):
        self._flows: Dict[str, FlowDefinition] = {}

    def register_flow(self, flow: FlowDefinition):
        """Register a flow definition."""
        self._flows[flow.name] = flow
        logger.info(f"Registered flow: {flow.name} with {len(flow.steps)} steps")

    def get_flow(self, name: str) -> Optional[FlowDefinition]:
        """Get flow definition by name."""
        return self._flows.get(name)

    async def get_active_flow(self, phone: str) -> Optional[FlowState]:
        """
        Check if user has an active flow.

        Args:
            phone: User's phone number

        Returns:
            FlowState if active flow exists, None otherwise
        """
        store = get_store()
        state_data = await store.get_flow_state(phone)

        if not state_data:
            return None

        try:
            # Handle nested structure from store
            if "flow_name" in state_data:
                return FlowState.from_dict(state_data)
            elif "collected_data" in state_data:
                # Already flat structure
                return FlowState(
                    flow_name=state_data.get("flow_name", ""),
                    current_step=state_data.get("current_step", ""),
                    collected_data=state_data.get("collected_data", {}),
                    attempts=state_data.get("attempts", 0)
                )
        except Exception as e:
            logger.error(f"Error parsing flow state: {e}")
            return None

        return None

    async def start_flow(
        self,
        phone: str,
        flow_name: str,
        initial_data: Dict[str, Any] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Start a new flow for user.

        Args:
            phone: User's phone number
            flow_name: Name of flow to start
            initial_data: Pre-filled data (e.g., from entity extraction)
            language: User's language for prompts

        Returns:
            Dict with:
                - started: bool
                - prompt: Next question to ask
                - flow_name: Name of started flow
                - error: Error message if failed
        """
        flow = self.get_flow(flow_name)
        if not flow:
            return {
                "started": False,
                "error": f"Unknown flow: {flow_name}"
            }

        # Clear any existing flow
        store = get_store()
        await store.clear_flow_state(phone)

        # Initialize with any pre-filled data
        collected_data = initial_data or {}

        # Find first step that needs input
        first_step = None
        for step in flow.steps:
            # Skip if already have data for this field
            if step.field_name in collected_data:
                continue
            # Skip if skip condition met
            if step.skip_if and step.skip_if(collected_data):
                continue
            first_step = step
            break

        if not first_step:
            # All data already collected!
            return {
                "started": True,
                "completed": True,
                "collected_data": collected_data,
                "flow_name": flow_name
            }

        # Save flow state
        await store.save_flow_state(
            phone=phone,
            flow_name=flow_name,
            current_step=first_step.name,
            collected_data=collected_data,
            expires_in_minutes=flow.timeout_minutes
        )

        # Get prompt for first step
        prompt = self._get_prompt(first_step, language)

        return {
            "started": True,
            "completed": False,
            "prompt": prompt,
            "step_name": first_step.name,
            "step_type": first_step.step_type.value,
            "examples": first_step.examples,
            "options": first_step.options,
            "flow_name": flow_name
        }

    async def process_input(
        self,
        phone: str,
        user_input: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process user input in active flow.

        Args:
            phone: User's phone number
            user_input: User's message
            language: User's language for prompts

        Returns:
            Dict with:
                - completed: bool (True if flow finished)
                - collected_data: All collected data (if completed)
                - prompt: Next question (if not completed)
                - validation_error: Error message (if validation failed)
                - no_active_flow: True if no flow active
        """
        # Get active flow state
        state = await self.get_active_flow(phone)
        if not state:
            return {"no_active_flow": True}

        flow = self.get_flow(state.flow_name)
        if not flow:
            return {"no_active_flow": True, "error": "Flow definition not found"}

        # Get current step
        current_step = flow.get_step(state.current_step)
        if not current_step:
            return {"error": f"Invalid step: {state.current_step}"}

        # Validate input
        validator = get_validator(current_step)
        validation = validator(user_input)

        store = get_store()

        if not validation.is_valid:
            # Increment attempts
            state.attempts += 1

            if state.attempts >= 3:
                # Too many attempts, cancel flow
                await store.clear_flow_state(phone)
                return {
                    "cancelled": True,
                    "reason": "too_many_attempts",
                    "message": "Too many invalid attempts. Please start over."
                }

            # Save state with incremented attempts
            await store.save_flow_state(
                phone=phone,
                flow_name=state.flow_name,
                current_step=state.current_step,
                collected_data=state.collected_data,
                expires_in_minutes=flow.timeout_minutes
            )

            # Return validation error
            retry_prompt = current_step.retry_prompt or validation.error_message
            return {
                "completed": False,
                "validation_error": validation.error_message,
                "prompt": retry_prompt,
                "suggestions": validation.suggestions,
                "attempts": state.attempts
            }

        # Valid input - store the value
        state.collected_data[current_step.field_name] = validation.parsed_value

        # Find next step
        next_step = flow.get_next_step(state.current_step, state.collected_data)

        if not next_step:
            # Flow complete!
            await store.clear_flow_state(phone)

            return {
                "completed": True,
                "collected_data": state.collected_data,
                "flow_name": state.flow_name,
                "on_complete": flow.on_complete
            }

        # Save state for next step
        await store.save_flow_state(
            phone=phone,
            flow_name=state.flow_name,
            current_step=next_step.name,
            collected_data=state.collected_data,
            expires_in_minutes=flow.timeout_minutes
        )

        # Get prompt for next step
        prompt = self._get_prompt(next_step, language)

        return {
            "completed": False,
            "prompt": prompt,
            "step_name": next_step.name,
            "step_type": next_step.step_type.value,
            "examples": next_step.examples,
            "options": next_step.options,
            "collected_so_far": state.collected_data
        }

    async def cancel_flow(self, phone: str) -> bool:
        """Cancel active flow for user."""
        store = get_store()
        return await store.clear_flow_state(phone)

    def _get_prompt(self, step: FlowStep, language: str = "en") -> str:
        """Get prompt text for step in specified language."""
        if isinstance(step.prompt, dict):
            # Multilingual prompt
            prompt = step.prompt.get(language) or step.prompt.get("en", "")
        else:
            prompt = step.prompt

        # Add examples if available
        if step.examples and "{examples}" not in prompt:
            examples_text = ", ".join(step.examples[:3])
            prompt = f"{prompt}\n(e.g., {examples_text})"

        # Add options if choice type
        if step.options and step.step_type.value == "choice":
            options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(step.options)])
            prompt = f"{prompt}\n{options_text}"

        return prompt

    async def is_in_flow(self, phone: str) -> bool:
        """Check if user is currently in a flow."""
        state = await self.get_active_flow(phone)
        return state is not None

    async def get_collected_data(self, phone: str) -> Dict[str, Any]:
        """Get data collected so far in active flow."""
        state = await self.get_active_flow(phone)
        return state.collected_data if state else {}


# =============================================================================
# SINGLETON
# =============================================================================

_flow_manager: Optional[FlowManager] = None


def get_flow_manager() -> FlowManager:
    """Get singleton FlowManager instance."""
    global _flow_manager
    if _flow_manager is None:
        _flow_manager = FlowManager()
        # Register built-in flows
        from common.flows.definitions import register_default_flows
        register_default_flows(_flow_manager)
    return _flow_manager
