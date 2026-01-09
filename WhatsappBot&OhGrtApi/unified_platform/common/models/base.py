"""
Base Pydantic models shared across applications.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel as PydanticBaseModel, Field


class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""

    model_config = {
        "extra": "ignore",
        "from_attributes": True,
    }


class WhatsAppMessage(BaseModel):
    """Represents a WhatsApp message."""

    message_id: str = Field(..., description="Unique message ID")
    from_number: str = Field(..., description="Sender's phone number")
    phone_number_id: str = Field(default="", description="WhatsApp phone number ID")
    timestamp: str = Field(default="", description="Message timestamp")
    message_type: str = Field(default="text", description="Message type")
    text: Optional[str] = Field(default=None, description="Message text content")
    media_id: Optional[str] = Field(default=None, description="Media ID for attachments")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Location data")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context data")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for processing."""
        return {
            "message_id": self.message_id,
            "from_number": self.from_number,
            "phone_number_id": self.phone_number_id,
            "timestamp": self.timestamp,
            "message_type": self.message_type,
            "text": self.text,
            "media_id": self.media_id,
            "location": self.location,
            "context": self.context,
        }


class APIResponse(BaseModel):
    """Standard API response model."""

    success: bool = Field(default=True, description="Whether the request was successful")
    message: str = Field(default="", description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class WeatherData(BaseModel):
    """Weather information model."""

    city: str = Field(..., description="City name")
    country: str = Field(default="", description="Country code")
    temperature: float = Field(..., description="Temperature in Celsius")
    feels_like: float = Field(default=0.0, description="Feels like temperature")
    humidity: int = Field(default=0, description="Humidity percentage")
    description: str = Field(default="", description="Weather description")
    icon: str = Field(default="", description="Weather icon code")
    wind_speed: float = Field(default=0.0, description="Wind speed in m/s")
    timestamp: Optional[datetime] = Field(default=None, description="Data timestamp")

    def format_message(self) -> str:
        """Format weather data as a readable message."""
        return (
            f"Weather in {self.city}, {self.country}:\n"
            f"Temperature: {self.temperature:.1f}C (feels like {self.feels_like:.1f}C)\n"
            f"Condition: {self.description}\n"
            f"Humidity: {self.humidity}%\n"
            f"Wind: {self.wind_speed} m/s"
        )


class NewsArticle(BaseModel):
    """News article model."""

    title: str = Field(..., description="Article title")
    description: Optional[str] = Field(default=None, description="Article description")
    url: str = Field(..., description="Article URL")
    source: str = Field(default="", description="Source name")
    published_at: Optional[datetime] = Field(default=None, description="Publication date")
    image_url: Optional[str] = Field(default=None, description="Article image URL")

    def format_message(self) -> str:
        """Format article as a readable message."""
        return f"*{self.title}*\n{self.description or ''}\nSource: {self.source}\n{self.url}"


class BotState(BaseModel):
    """
    Base state for LangGraph workflow.

    This can be extended by individual applications.
    """

    current_query: str = Field(default="", description="User's current message")
    user_phone: str = Field(default="", description="User's phone number")
    user_id: Optional[str] = Field(default=None, description="User ID (for API)")
    intent: str = Field(default="unknown", description="Detected intent")
    extracted_entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities from message"
    )
    response_text: str = Field(default="", description="Response to send")
    response_type: str = Field(default="text", description="Response type")
    response_media_url: Optional[str] = Field(default=None, description="Media URL")
    should_fallback: bool = Field(default=False, description="Use fallback handler")
    error: Optional[str] = Field(default=None, description="Error message")
    tool_result: Optional[Dict[str, Any]] = Field(default=None, description="Tool result")
    route_log: List[str] = Field(default_factory=list, description="Routing history")
    language: str = Field(default="en", description="Detected language")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
