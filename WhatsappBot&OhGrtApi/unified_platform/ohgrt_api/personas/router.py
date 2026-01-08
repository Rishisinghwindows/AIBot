"""Router for persona endpoints."""

import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from ohgrt_api.db.base import get_db
from ohgrt_api.db.models import User, Persona
from ohgrt_api.personas.schemas import (
    HandleCheckResponse,
    PersonaChatRequest,
    PersonaChatResponse,
    PersonaChatHistoryResponse,
    PersonaCreateRequest,
    PersonaDocumentResponse,
    PersonaPublicResponse,
    PersonaResponse,
    PersonaUpdateRequest,
)
from ohgrt_api.personas.service import PersonaService
from ohgrt_api.logger import logger
from ohgrt_api.config import get_settings


router = APIRouter(prefix="/personas", tags=["personas"])


# --- Authenticated endpoints ---

@router.get("/check-handle/{handle}", response_model=HandleCheckResponse)
async def check_handle_availability(
    handle: str,
    db: Session = Depends(get_db),
) -> HandleCheckResponse:
    """Check if a handle is available (no auth required)."""
    service = PersonaService(db)
    available = service.check_handle_available(handle)
    return HandleCheckResponse(handle=handle.lower(), available=available)


@router.post("", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    request: PersonaCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
) -> PersonaResponse:
    """Create a new AI persona."""
    service = PersonaService(db)

    try:
        persona = service.create_persona(user.id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PersonaResponse(
        id=str(persona.id),
        handle=persona.handle,
        display_name=persona.display_name,
        tagline=persona.tagline,
        avatar_url=persona.avatar_url,
        personality=persona.personality,
        professional=persona.professional,
        is_public=persona.is_public,
        total_chats=persona.total_chats,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
    )


@router.get("", response_model=List[PersonaResponse])
async def list_personas(
    db: Session = Depends(get_db),
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
) -> List[PersonaResponse]:
    """List all personas for the current user."""
    service = PersonaService(db)
    personas = service.get_user_personas(user.id)

    return [
        PersonaResponse(
            id=str(p.id),
            handle=p.handle,
            display_name=p.display_name,
            tagline=p.tagline,
            avatar_url=p.avatar_url,
            personality=p.personality,
            professional=p.professional,
            is_public=p.is_public,
            total_chats=p.total_chats,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in personas
    ]


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
) -> PersonaResponse:
    """Get a specific persona by ID."""
    service = PersonaService(db)

    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid persona ID")

    persona = service.get_persona_by_id(pid)
    if not persona or persona.user_id != user.id:
        raise HTTPException(status_code=404, detail="Persona not found")

    return PersonaResponse(
        id=str(persona.id),
        handle=persona.handle,
        display_name=persona.display_name,
        tagline=persona.tagline,
        avatar_url=persona.avatar_url,
        personality=persona.personality,
        professional=persona.professional,
        is_public=persona.is_public,
        total_chats=persona.total_chats,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
    )


@router.put("/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: str,
    request: PersonaUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
) -> PersonaResponse:
    """Update a persona."""
    service = PersonaService(db)

    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid persona ID")

    persona = service.update_persona(pid, user.id, request)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    return PersonaResponse(
        id=str(persona.id),
        handle=persona.handle,
        display_name=persona.display_name,
        tagline=persona.tagline,
        avatar_url=persona.avatar_url,
        personality=persona.personality,
        professional=persona.professional,
        is_public=persona.is_public,
        total_chats=persona.total_chats,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
    )


@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
) -> dict:
    """Delete a persona."""
    service = PersonaService(db)

    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid persona ID")

    deleted = service.delete_persona(pid, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Persona not found")

    return {"message": "Persona deleted"}


# --- Document endpoints ---

@router.post("/{persona_id}/documents", response_model=PersonaDocumentResponse)
async def upload_document(
    persona_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
) -> PersonaDocumentResponse:
    """Upload a document to train a persona."""
    service = PersonaService(db)
    settings = get_settings()

    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid persona ID")

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    allowed_extensions = [".pdf", ".txt", ".md", ".docx"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Check file size (max 10MB)
    content = await file.read()
    file_size = len(content)
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    # Save file
    upload_dir = f"/data/personas/{persona_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Add to database
    doc = service.add_document(
        persona_id=pid,
        user_id=user.id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        chunk_count=0,  # Will be updated after RAG processing
    )

    if not doc:
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=404, detail="Persona not found")

    # TODO: Trigger RAG processing for the document
    # This would chunk the document and add to vector store

    return PersonaDocumentResponse(
        id=str(doc.id),
        filename=doc.filename,
        file_size=doc.file_size,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
    )


@router.get("/{persona_id}/documents", response_model=List[PersonaDocumentResponse])
async def list_documents(
    persona_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
) -> List[PersonaDocumentResponse]:
    """List all documents for a persona."""
    service = PersonaService(db)

    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid persona ID")

    docs = service.get_persona_documents(pid, user.id)

    return [
        PersonaDocumentResponse(
            id=str(d.id),
            filename=d.filename,
            file_size=d.file_size,
            chunk_count=d.chunk_count,
            created_at=d.created_at,
        )
        for d in docs
    ]


@router.delete("/{persona_id}/documents/{doc_id}")
async def delete_document(
    persona_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
) -> dict:
    """Delete a document from a persona."""
    service = PersonaService(db)

    try:
        pid = uuid.UUID(persona_id)
        did = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    deleted = service.delete_document(did, pid, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document deleted"}


# --- Public endpoints (no auth required) ---

public_router = APIRouter(prefix="/p", tags=["public-personas"])


@public_router.get("/{handle}", response_model=PersonaPublicResponse)
async def get_public_persona(
    handle: str,
    db: Session = Depends(get_db),
) -> PersonaPublicResponse:
    """Get a public persona profile by handle."""
    service = PersonaService(db)
    persona = service.get_persona_by_handle(handle)

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    personality = persona.personality or {}
    professional = persona.professional or {}

    return PersonaPublicResponse(
        handle=persona.handle,
        display_name=persona.display_name,
        tagline=persona.tagline,
        avatar_url=persona.avatar_url,
        expertise_area=personality.get("expertise_area"),
        topics=personality.get("topics"),
        job_title=professional.get("job_title"),
        industry=professional.get("industry"),
    )


@public_router.post("/{handle}/chat", response_model=PersonaChatResponse)
async def chat_with_persona(
    handle: str,
    request: PersonaChatRequest,
    db: Session = Depends(get_db),
) -> PersonaChatResponse:
    """Send a message to a persona and get a response."""
    from langchain_anthropic import ChatAnthropic
    from langchain.schema import HumanMessage, SystemMessage, AIMessage

    service = PersonaService(db)
    settings = get_settings()

    persona = service.get_persona_by_handle(handle)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Get or create chat session
    chat = service.get_or_create_chat(
        persona_id=persona.id,
        session_id=request.session_id,
        visitor_name=request.visitor_name,
    )

    # Get chat history
    history = service.get_chat_history(chat.id, limit=20)

    # Build messages for LLM
    messages = []

    # System prompt
    if persona.system_prompt:
        messages.append(SystemMessage(content=persona.system_prompt))
    else:
        messages.append(SystemMessage(content=f"You are {persona.display_name}. {persona.tagline or ''}"))

    # Add history
    for msg in history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))

    # Add current message
    messages.append(HumanMessage(content=request.message))

    # Save user message
    service.add_chat_message(chat.id, "user", request.message)

    # Generate response
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=1024,
        )
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logger.error("persona_chat_error", error=str(e), persona=handle)
        response_text = "I'm having trouble responding right now. Please try again."

    # Save assistant message
    service.add_chat_message(chat.id, "assistant", response_text)

    return PersonaChatResponse(
        session_id=chat.visitor_session,
        response=response_text,
    )


@public_router.get("/{handle}/chat/{session_id}", response_model=PersonaChatHistoryResponse)
async def get_chat_history(
    handle: str,
    session_id: str,
    db: Session = Depends(get_db),
) -> PersonaChatHistoryResponse:
    """Get chat history for a session."""
    service = PersonaService(db)

    persona = service.get_persona_by_handle(handle)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    chat = service.get_chat_by_session(persona.id, session_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat session not found")

    history = service.get_chat_history(chat.id)

    return PersonaChatHistoryResponse(
        session_id=session_id,
        persona_handle=handle,
        messages=[
            {"role": msg.role, "content": msg.content, "created_at": msg.created_at.isoformat()}
            for msg in history
        ],
        created_at=chat.created_at,
    )
