"""
Step-Based Conversation Flows

Declarative, multi-turn conversation flows for collecting user data.
Each flow defines steps, validation, and transitions.

Usage:
    from common.flows import FlowManager, get_flow_manager

    # Check if user is in a flow
    flow_state = await flow_manager.get_active_flow(phone)

    # Start a new flow
    response = await flow_manager.start_flow(phone, "life_prediction")

    # Process user input in flow
    result = await flow_manager.process_input(phone, user_message)
    if result["completed"]:
        # Flow finished, result["collected_data"] has all data
    else:
        # Send result["prompt"] to user
"""

from common.flows.base import (
    FlowStep,
    FlowDefinition,
    FlowState,
    StepType,
    ValidationResult,
)
from common.flows.flow_manager import FlowManager, get_flow_manager
from common.flows.definitions import (
    BIRTH_DETAILS_FLOW,
    LIFE_PREDICTION_FLOW,
    KUNDLI_MATCHING_FLOW,
    DOSHA_CHECK_FLOW,
)

__all__ = [
    # Core classes
    "FlowStep",
    "FlowDefinition",
    "FlowState",
    "StepType",
    "ValidationResult",

    # Manager
    "FlowManager",
    "get_flow_manager",

    # Pre-defined flows
    "BIRTH_DETAILS_FLOW",
    "LIFE_PREDICTION_FLOW",
    "KUNDLI_MATCHING_FLOW",
    "DOSHA_CHECK_FLOW",
]
