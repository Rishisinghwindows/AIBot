from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


class RouterCategory(str, Enum):
    weather = "weather"
    pdf = "pdf"
    sql = "sql"
    gmail = "gmail"
    image = "image"
    help = "help"
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
