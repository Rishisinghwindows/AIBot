"""Pydantic schemas for personas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PersonalityQuestionnaire(BaseModel):
    """Personality questionnaire data."""
    communication_style: Optional[str] = Field(None, description="formal, casual, professional, friendly")
    expertise_area: Optional[str] = Field(None, description="Primary area of expertise")
    topics: Optional[List[str]] = Field(default_factory=list, description="Topics knowledgeable about")
    outside_expertise_response: Optional[str] = Field(None, description="How to respond to questions outside expertise")
    response_length: Optional[str] = Field(None, description="brief, moderate, detailed")
    use_humor: Optional[str] = Field(None, description="never, sometimes, often")


class ProfessionalQuestionnaire(BaseModel):
    """Professional questionnaire data."""
    job_title: Optional[str] = None
    industry: Optional[str] = None
    years_experience: Optional[int] = None
    skills: Optional[List[str]] = Field(default_factory=list)
    achievements: Optional[str] = None
    problems_solved: Optional[str] = Field(None, description="What problems do you help solve?")


class PersonaCreateRequest(BaseModel):
    """Request to create a new persona."""
    handle: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    display_name: str = Field(..., min_length=1, max_length=100)
    tagline: Optional[str] = Field(None, max_length=200)
    avatar_url: Optional[str] = None
    personality: Optional[PersonalityQuestionnaire] = None
    professional: Optional[ProfessionalQuestionnaire] = None
    is_public: bool = True


class PersonaUpdateRequest(BaseModel):
    """Request to update a persona."""
    display_name: Optional[str] = Field(None, max_length=100)
    tagline: Optional[str] = Field(None, max_length=200)
    avatar_url: Optional[str] = None
    personality: Optional[PersonalityQuestionnaire] = None
    professional: Optional[ProfessionalQuestionnaire] = None
    is_public: Optional[bool] = None


class PersonaResponse(BaseModel):
    """Persona response."""
    id: str
    handle: str
    display_name: str
    tagline: Optional[str] = None
    avatar_url: Optional[str] = None
    personality: Optional[dict] = None
    professional: Optional[dict] = None
    is_public: bool
    total_chats: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PersonaPublicResponse(BaseModel):
    """Public persona response (for visitors)."""
    handle: str
    display_name: str
    tagline: Optional[str] = None
    avatar_url: Optional[str] = None
    expertise_area: Optional[str] = None
    topics: Optional[List[str]] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None


class PersonaDocumentResponse(BaseModel):
    """Persona document response."""
    id: str
    filename: str
    file_size: int
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class PersonaChatRequest(BaseModel):
    """Request to chat with a persona."""
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    visitor_name: Optional[str] = Field(None, max_length=100)


class PersonaChatResponse(BaseModel):
    """Response from persona chat."""
    session_id: str
    response: str


class PersonaChatHistoryResponse(BaseModel):
    """Chat history response."""
    session_id: str
    persona_handle: str
    messages: List[dict]
    created_at: datetime


class HandleCheckResponse(BaseModel):
    """Response for handle availability check."""
    handle: str
    available: bool
