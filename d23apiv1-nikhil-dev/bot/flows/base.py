"""
Base Classes for Step-Based Flows

Defines the building blocks for declarative conversation flows.
"""

import re
import logging
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class StepType(Enum):
    """Type of input expected at a step."""
    TEXT = "text"                    # Free text input
    DATE = "date"                    # Birth date (DD-MM-YYYY)
    TIME = "time"                    # Time (HH:MM AM/PM)
    PLACE = "place"                  # Place name
    CHOICE = "choice"                # Selection from options
    CONFIRMATION = "confirmation"     # Yes/No
    NAME = "name"                    # Person's name


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    parsed_value: Any = None         # Normalized/parsed value
    error_message: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)


@dataclass
class FlowStep:
    """
    A single step in a conversation flow.

    Attributes:
        name: Unique identifier for this step
        prompt: Message to show user (can be dict for multilingual)
        prompt_key: Key for i18n template lookup
        step_type: Type of input expected
        field_name: Name of field to store in collected_data
        required: Whether this step must be completed
        validator: Custom validation function
        options: For CHOICE type, list of valid options
        examples: Example inputs to show user
        retry_prompt: Message on validation failure
        skip_if: Condition to skip this step
    """
    name: str
    prompt: Union[str, Dict[str, str]]  # str or {lang_code: message}
    prompt_key: Optional[str] = None     # For i18n lookup
    step_type: StepType = StepType.TEXT
    field_name: Optional[str] = None     # Defaults to step name
    required: bool = True
    validator: Optional[Callable[[str], ValidationResult]] = None
    options: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    retry_prompt: Optional[str] = None
    skip_if: Optional[Callable[[Dict], bool]] = None

    def __post_init__(self):
        if self.field_name is None:
            self.field_name = self.name


@dataclass
class FlowDefinition:
    """
    Definition of a complete conversation flow.

    Attributes:
        name: Unique flow identifier
        description: Human-readable description
        steps: Ordered list of steps
        on_complete: Action to take when flow completes
        timeout_minutes: How long before flow expires
        allow_restart: Whether user can restart mid-flow
    """
    name: str
    description: str
    steps: List[FlowStep]
    on_complete: Optional[str] = None    # Intent/action to trigger
    timeout_minutes: int = 10
    allow_restart: bool = True

    def get_step(self, name: str) -> Optional[FlowStep]:
        """Get step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def get_step_index(self, name: str) -> int:
        """Get index of step by name."""
        for i, step in enumerate(self.steps):
            if step.name == name:
                return i
        return -1

    def get_next_step(self, current: str, collected_data: Dict) -> Optional[FlowStep]:
        """Get next step after current, respecting skip conditions."""
        current_idx = self.get_step_index(current)
        if current_idx < 0:
            return self.steps[0] if self.steps else None

        for step in self.steps[current_idx + 1:]:
            # Check skip condition
            if step.skip_if and step.skip_if(collected_data):
                continue
            return step
        return None  # Flow complete


@dataclass
class FlowState:
    """
    Current state of a user's flow.

    Attributes:
        flow_name: Name of the active flow
        current_step: Current step name
        collected_data: Data collected so far
        attempts: Number of attempts at current step
        started_at: When flow started
        last_activity: Last user interaction
    """
    flow_name: str
    current_step: str
    collected_data: Dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "flow_name": self.flow_name,
            "current_step": self.current_step,
            "collected_data": self.collected_data,
            "attempts": self.attempts,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FlowState":
        """Create from dictionary."""
        return cls(
            flow_name=data["flow_name"],
            current_step=data["current_step"],
            collected_data=data.get("collected_data", {}),
            attempts=data.get("attempts", 0),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else None,
        )


# =============================================================================
# BUILT-IN VALIDATORS
# =============================================================================

def validate_date(input_text: str) -> ValidationResult:
    """
    Validate and parse date input.
    Accepts: DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD
    """
    input_text = input_text.strip()

    # Common date patterns
    patterns = [
        (r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", "dmy"),      # DD-MM-YYYY
        (r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", "ymd"),      # YYYY-MM-DD
        (r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2})", "dmy_short"), # DD-MM-YY
    ]

    for pattern, fmt in patterns:
        match = re.match(pattern, input_text)
        if match:
            groups = match.groups()
            try:
                if fmt == "dmy":
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                elif fmt == "ymd":
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                else:  # dmy_short
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                    year = 1900 + year if year > 50 else 2000 + year

                # Validate ranges
                if not (1 <= month <= 12):
                    return ValidationResult(False, error_message="Invalid month. Please use 1-12.")
                if not (1 <= day <= 31):
                    return ValidationResult(False, error_message="Invalid day. Please use 1-31.")
                if not (1900 <= year <= 2100):
                    return ValidationResult(False, error_message="Invalid year. Please use 1900-2100.")

                # Return normalized format
                normalized = f"{day:02d}-{month:02d}-{year}"
                return ValidationResult(True, parsed_value=normalized)

            except ValueError:
                pass

    return ValidationResult(
        False,
        error_message="Please provide date in DD-MM-YYYY format.",
        suggestions=["15-08-1990", "01-01-1985", "25-12-2000"]
    )


def validate_time(input_text: str) -> ValidationResult:
    """
    Validate and parse time input.
    Accepts: HH:MM AM/PM, HH:MM, HHMM
    """
    input_text = input_text.strip().upper()

    # Common time patterns
    patterns = [
        r"(\d{1,2})[:\.](\d{2})\s*(AM|PM)",      # HH:MM AM/PM
        r"(\d{1,2})[:\.](\d{2})",                 # HH:MM (24-hour)
        r"(\d{1,2})\s*(AM|PM)",                   # H AM/PM
    ]

    for i, pattern in enumerate(patterns):
        match = re.match(pattern, input_text)
        if match:
            groups = match.groups()
            try:
                if i == 0:  # HH:MM AM/PM
                    hour, minute, meridiem = int(groups[0]), int(groups[1]), groups[2]
                    if meridiem == "PM" and hour != 12:
                        hour += 12
                    elif meridiem == "AM" and hour == 12:
                        hour = 0
                elif i == 1:  # HH:MM (24-hour)
                    hour, minute = int(groups[0]), int(groups[1])
                else:  # H AM/PM
                    hour, meridiem = int(groups[0]), groups[1]
                    minute = 0
                    if meridiem == "PM" and hour != 12:
                        hour += 12
                    elif meridiem == "AM" and hour == 12:
                        hour = 0

                # Validate ranges
                if not (0 <= hour <= 23):
                    return ValidationResult(False, error_message="Invalid hour. Please use 1-12 AM/PM or 0-23.")
                if not (0 <= minute <= 59):
                    return ValidationResult(False, error_message="Invalid minute. Please use 0-59.")

                # Return in 12-hour format
                meridiem = "AM" if hour < 12 else "PM"
                display_hour = hour if hour <= 12 else hour - 12
                if display_hour == 0:
                    display_hour = 12
                normalized = f"{display_hour}:{minute:02d} {meridiem}"
                return ValidationResult(True, parsed_value=normalized)

            except ValueError:
                pass

    return ValidationResult(
        False,
        error_message="Please provide time like 10:30 AM or 14:30.",
        suggestions=["10:30 AM", "6:00 PM", "14:30"]
    )


def validate_place(input_text: str) -> ValidationResult:
    """
    Validate place name.
    Basic validation - at least 2 characters, no numbers only.
    """
    input_text = input_text.strip()

    if len(input_text) < 2:
        return ValidationResult(False, error_message="Place name too short. Please provide city/town name.")

    if input_text.isdigit():
        return ValidationResult(False, error_message="Please provide a place name, not a number.")

    # Clean up common issues
    cleaned = input_text.title()
    return ValidationResult(True, parsed_value=cleaned)


def validate_name(input_text: str) -> ValidationResult:
    """
    Validate person's name.
    At least 2 characters, letters and spaces only.
    """
    input_text = input_text.strip()

    if len(input_text) < 2:
        return ValidationResult(False, error_message="Name too short.")

    # Allow letters, spaces, and some special characters
    if not re.match(r"^[\w\s.'-]+$", input_text, re.UNICODE):
        return ValidationResult(False, error_message="Please provide a valid name.")

    return ValidationResult(True, parsed_value=input_text.title())


def validate_confirmation(input_text: str) -> ValidationResult:
    """
    Validate yes/no confirmation.
    """
    input_text = input_text.strip().lower()

    yes_words = ["yes", "y", "yeah", "yep", "sure", "ok", "okay", "ha", "haan", "ji"]
    no_words = ["no", "n", "nope", "nah", "na", "nahi"]

    if input_text in yes_words:
        return ValidationResult(True, parsed_value=True)
    if input_text in no_words:
        return ValidationResult(True, parsed_value=False)

    return ValidationResult(
        False,
        error_message="Please reply with Yes or No.",
        suggestions=["Yes", "No"]
    )


def validate_choice(options: List[str]):
    """
    Create validator for choice from options.
    """
    def validator(input_text: str) -> ValidationResult:
        input_lower = input_text.strip().lower()

        # Check exact match (case-insensitive)
        for opt in options:
            if opt.lower() == input_lower:
                return ValidationResult(True, parsed_value=opt)

        # Check partial match
        matches = [opt for opt in options if input_lower in opt.lower()]
        if len(matches) == 1:
            return ValidationResult(True, parsed_value=matches[0])

        # Check by number (1, 2, 3...)
        if input_text.isdigit():
            idx = int(input_text) - 1
            if 0 <= idx < len(options):
                return ValidationResult(True, parsed_value=options[idx])

        return ValidationResult(
            False,
            error_message=f"Please choose from: {', '.join(options)}",
            suggestions=options[:4]  # Show first 4 options
        )

    return validator


# =============================================================================
# DEFAULT VALIDATORS BY STEP TYPE
# =============================================================================

DEFAULT_VALIDATORS = {
    StepType.DATE: validate_date,
    StepType.TIME: validate_time,
    StepType.PLACE: validate_place,
    StepType.NAME: validate_name,
    StepType.CONFIRMATION: validate_confirmation,
    StepType.TEXT: lambda x: ValidationResult(True, parsed_value=x.strip()),
}


def get_validator(step: FlowStep) -> Callable[[str], ValidationResult]:
    """Get appropriate validator for a step."""
    if step.validator:
        return step.validator

    if step.step_type == StepType.CHOICE and step.options:
        return validate_choice(step.options)

    return DEFAULT_VALIDATORS.get(
        step.step_type,
        lambda x: ValidationResult(True, parsed_value=x.strip())
    )
