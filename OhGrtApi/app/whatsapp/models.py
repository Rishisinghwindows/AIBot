"""
Pydantic Models for WhatsApp Webhook Payloads

Based on Meta WhatsApp Cloud API webhook structure.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class Profile(BaseModel):
    """User profile information."""
    name: str


class Contact(BaseModel):
    """Contact information from webhook."""
    profile: Profile
    wa_id: str


class TextContent(BaseModel):
    """Text message content."""
    body: str


class ImageContent(BaseModel):
    """Image message content."""
    caption: Optional[str] = None
    mime_type: str
    sha256: str
    id: str


class AudioContent(BaseModel):
    """Audio message content."""
    mime_type: str
    sha256: str
    id: str
    voice: Optional[bool] = False


class DocumentContent(BaseModel):
    """Document message content."""
    caption: Optional[str] = None
    filename: str
    mime_type: str
    sha256: str
    id: str


class LocationContent(BaseModel):
    """Location message content."""
    latitude: float
    longitude: float
    name: Optional[str] = None
    address: Optional[str] = None


class ButtonReply(BaseModel):
    """Button reply content."""
    id: str
    title: str


class ListReply(BaseModel):
    """List reply content."""
    id: str
    title: str
    description: Optional[str] = None


class Interactive(BaseModel):
    """Interactive message content."""
    type: str
    button_reply: Optional[ButtonReply] = None
    list_reply: Optional[ListReply] = None


class Context(BaseModel):
    """Message context (for replies)."""
    from_: Optional[str] = Field(None, alias="from")
    id: Optional[str] = None
    referred_product: Optional[dict] = None

    class Config:
        populate_by_name = True


class Message(BaseModel):
    """Individual message from webhook."""
    from_: str = Field(..., alias="from")
    id: str
    timestamp: str
    type: str
    text: Optional[TextContent] = None
    image: Optional[ImageContent] = None
    audio: Optional[AudioContent] = None
    document: Optional[DocumentContent] = None
    location: Optional[LocationContent] = None
    interactive: Optional[Interactive] = None
    context: Optional[Context] = None
    errors: Optional[List[dict]] = None

    class Config:
        populate_by_name = True


class Status(BaseModel):
    """Message status update."""
    id: str
    status: str  # sent, delivered, read, failed
    timestamp: str
    recipient_id: str
    conversation: Optional[dict] = None
    pricing: Optional[dict] = None
    errors: Optional[List[dict]] = None


class Metadata(BaseModel):
    """Webhook metadata."""
    display_phone_number: str
    phone_number_id: str


class Value(BaseModel):
    """Webhook value containing messages or statuses."""
    messaging_product: str
    metadata: Metadata
    contacts: Optional[List[Contact]] = None
    messages: Optional[List[Message]] = None
    statuses: Optional[List[Status]] = None


class Change(BaseModel):
    """Webhook change entry."""
    value: Value
    field: str


class Entry(BaseModel):
    """Webhook entry."""
    id: str
    changes: List[Change]


class WebhookPayload(BaseModel):
    """Root webhook payload from Meta."""
    object: str
    entry: List[Entry]


# Extracted message dict for processing
class ExtractedMessage:
    """Simplified message structure for processing."""

    def __init__(
        self,
        message_id: str,
        from_number: str,
        phone_number_id: str,
        timestamp: str,
        message_type: str,
        text: Optional[str] = None,
        media_id: Optional[str] = None,
        user_name: Optional[str] = None,
    ):
        self.message_id = message_id
        self.from_number = from_number
        self.phone_number_id = phone_number_id
        self.timestamp = timestamp
        self.message_type = message_type
        self.text = text
        self.media_id = media_id
        self.user_name = user_name

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "from_number": self.from_number,
            "phone_number_id": self.phone_number_id,
            "timestamp": self.timestamp,
            "message_type": self.message_type,
            "text": self.text,
            "media_id": self.media_id,
            "user_name": self.user_name,
        }


def extract_message(payload: WebhookPayload) -> Optional[ExtractedMessage]:
    """
    Extract message data from webhook payload.

    Args:
        payload: Parsed webhook payload

    Returns:
        ExtractedMessage or None if no message
    """
    for entry in payload.entry:
        for change in entry.changes:
            value = change.value

            # Skip status updates
            if value.messages is None:
                continue

            # Get user name from contacts
            user_name = None
            if value.contacts and len(value.contacts) > 0:
                user_name = value.contacts[0].profile.name

            for msg in value.messages:
                # Get text content
                text = None
                if msg.type == "text" and msg.text:
                    text = msg.text.body
                elif msg.interactive:
                    if msg.interactive.button_reply:
                        text = msg.interactive.button_reply.title
                    elif msg.interactive.list_reply:
                        text = msg.interactive.list_reply.title

                # Get media ID if present
                media_id = None
                if msg.type == "image" and msg.image:
                    media_id = msg.image.id
                elif msg.audio:
                    media_id = msg.audio.id
                elif msg.document:
                    media_id = msg.document.id

                return ExtractedMessage(
                    message_id=msg.id,
                    from_number=msg.from_,
                    phone_number_id=value.metadata.phone_number_id,
                    timestamp=msg.timestamp,
                    message_type=msg.type,
                    text=text,
                    media_id=media_id,
                    user_name=user_name,
                )

    return None


def is_status_update(payload: WebhookPayload) -> bool:
    """
    Check if payload is a status update (not a message).

    Args:
        payload: Parsed webhook payload

    Returns:
        True if this is a status update
    """
    for entry in payload.entry:
        for change in entry.changes:
            if change.value.statuses:
                return True
    return False
