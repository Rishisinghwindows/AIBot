from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, TypedDict,Any
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic import BaseModel, Field


class RouterCategory(str, Enum):
    weather = "weather"
    pdf = "pdf"
    sql = "sql"
    gmail = "gmail"
    chat = "chat"


class AgentState(TypedDict, total=False):
    message: str
    category: str
    response: str
    metadata: Dict[str, str]
    route_log: List[str]


class AskRequest(BaseModel):
    message: str = Field(..., description="User input to be routed")


class AskResponse(BaseModel):
    category: RouterCategory
    response: str
    route_log: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)


class WeatherResponse(BaseModel):
    city: str
    temperature_c: float
    humidity: float
    condition: str
    raw: Dict[str, object]


class PDFIngestResponse(BaseModel):
    filename: str
    chunks: int
    status: str
    vector_table: str


class EmailQuery(BaseModel):
    sender: Optional[str] = None
    subject: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    unread: bool = False


# Profile models
class ProfileBase(BaseModel):
    email: str = Field(..., example="user@example.com")
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")

class ProfileCreate(ProfileBase):
    pass

class Profile(ProfileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Conversation models
class Conversation(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Message models
class ChatMessage(BaseModel):
    id: UUID
    conversation_id: UUID
    from_actor: str
    text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Source models
class SourceCore(BaseModel):
    type: str = Field(..., example="file")
    path: Optional[str] = Field(None, example="/path/to/file.pdf")
    content: Optional[str] = Field(None, example="This is a text snippet.")
    filename: Optional[str] = Field(None, example="file.pdf")

class SourceCreate(SourceCore):
    pass

class Source(SourceCore):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Tool models
class ToolCore(BaseModel):
    name: str
    config: Optional[Dict[str, Any]] = None
    enabled: bool = True

class ToolCreate(ToolCore):
    pass

class ToolUpdate(ToolCore):
    pass

class Tool(ToolCore):
    id: UUID
    user_id: UUID
    api_key_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str