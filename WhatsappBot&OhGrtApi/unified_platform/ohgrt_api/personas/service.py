"""Service layer for persona operations."""

import os
import uuid
import secrets
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session

from ohgrt_api.db.models import Persona, PersonaDocument, PersonaChat, PersonaChatMessage
from ohgrt_api.personas.schemas import PersonaCreateRequest, PersonaUpdateRequest
from ohgrt_api.logger import logger


def generate_system_prompt(persona: Persona) -> str:
    """Generate a system prompt from persona questionnaire data."""
    personality = persona.personality or {}
    professional = persona.professional or {}

    parts = []

    # Identity
    parts.append(f"You are {persona.display_name}.")

    if persona.tagline:
        parts.append(persona.tagline)

    # Professional background
    if professional.get("job_title"):
        exp_str = ""
        if professional.get("years_experience"):
            exp_str = f" with {professional['years_experience']} years of experience"
        industry_str = ""
        if professional.get("industry"):
            industry_str = f" in {professional['industry']}"
        parts.append(f"You work as a {professional['job_title']}{exp_str}{industry_str}.")

    # Skills
    if professional.get("skills"):
        skills_list = ", ".join(professional["skills"][:5])
        parts.append(f"Your key skills include: {skills_list}.")

    # Communication style
    style = personality.get("communication_style", "professional")
    length = personality.get("response_length", "moderate")
    parts.append(f"Your communication style is {style} and you give {length} responses.")

    # Topics of expertise
    if personality.get("topics"):
        topics_list = ", ".join(personality["topics"][:5])
        parts.append(f"Your expertise includes: {topics_list}.")

    # Expertise area
    if personality.get("expertise_area"):
        parts.append(f"Your primary expertise is in {personality['expertise_area']}.")

    # Humor
    humor = personality.get("use_humor", "sometimes")
    if humor == "never":
        parts.append("You maintain a serious tone and avoid humor.")
    elif humor == "often":
        parts.append("You often use humor and wit in your responses.")

    # Outside expertise handling
    if personality.get("outside_expertise_response"):
        parts.append(f"When asked about topics outside your expertise, you {personality['outside_expertise_response']}.")

    # What you help with
    if professional.get("problems_solved"):
        parts.append(f"You help people with: {professional['problems_solved']}.")

    # Achievements
    if professional.get("achievements"):
        parts.append(f"Notable credentials: {professional['achievements']}.")

    return " ".join(parts)


class PersonaService:
    """Service for managing personas."""

    def __init__(self, db: Session):
        self.db = db

    def check_handle_available(self, handle: str) -> bool:
        """Check if a handle is available."""
        existing = self.db.query(Persona).filter(Persona.handle == handle.lower()).first()
        return existing is None

    def create_persona(self, user_id: uuid.UUID, data: PersonaCreateRequest) -> Persona:
        """Create a new persona."""
        handle = data.handle.lower()

        # Check handle availability
        if not self.check_handle_available(handle):
            raise ValueError(f"Handle '{handle}' is already taken")

        persona = Persona(
            user_id=user_id,
            handle=handle,
            display_name=data.display_name,
            tagline=data.tagline,
            avatar_url=data.avatar_url,
            personality=data.personality.model_dump() if data.personality else {},
            professional=data.professional.model_dump() if data.professional else {},
            is_public=data.is_public,
        )

        # Generate system prompt
        persona.system_prompt = generate_system_prompt(persona)

        self.db.add(persona)
        self.db.commit()
        self.db.refresh(persona)

        logger.info("persona_created", persona_id=str(persona.id), handle=handle)
        return persona

    def get_user_personas(self, user_id: uuid.UUID) -> List[Persona]:
        """Get all personas for a user."""
        return (
            self.db.query(Persona)
            .filter(Persona.user_id == user_id)
            .order_by(Persona.created_at.desc())
            .all()
        )

    def get_persona_by_id(self, persona_id: uuid.UUID) -> Optional[Persona]:
        """Get persona by ID."""
        return self.db.query(Persona).filter(Persona.id == persona_id).first()

    def get_persona_by_handle(self, handle: str) -> Optional[Persona]:
        """Get persona by handle (public access)."""
        return (
            self.db.query(Persona)
            .filter(Persona.handle == handle.lower(), Persona.is_public == True)
            .first()
        )

    def update_persona(
        self, persona_id: uuid.UUID, user_id: uuid.UUID, data: PersonaUpdateRequest
    ) -> Optional[Persona]:
        """Update a persona."""
        persona = (
            self.db.query(Persona)
            .filter(Persona.id == persona_id, Persona.user_id == user_id)
            .first()
        )
        if not persona:
            return None

        if data.display_name is not None:
            persona.display_name = data.display_name
        if data.tagline is not None:
            persona.tagline = data.tagline
        if data.avatar_url is not None:
            persona.avatar_url = data.avatar_url
        if data.personality is not None:
            persona.personality = data.personality.model_dump()
        if data.professional is not None:
            persona.professional = data.professional.model_dump()
        if data.is_public is not None:
            persona.is_public = data.is_public

        # Regenerate system prompt
        persona.system_prompt = generate_system_prompt(persona)

        self.db.commit()
        self.db.refresh(persona)

        logger.info("persona_updated", persona_id=str(persona.id))
        return persona

    def delete_persona(self, persona_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a persona."""
        deleted = (
            self.db.query(Persona)
            .filter(Persona.id == persona_id, Persona.user_id == user_id)
            .delete()
        )
        self.db.commit()
        logger.info("persona_deleted", persona_id=str(persona_id), deleted=deleted > 0)
        return deleted > 0

    def add_document(
        self,
        persona_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
        file_size: int,
        chunk_count: int = 0,
    ) -> Optional[PersonaDocument]:
        """Add a document to a persona."""
        # Verify ownership
        persona = (
            self.db.query(Persona)
            .filter(Persona.id == persona_id, Persona.user_id == user_id)
            .first()
        )
        if not persona:
            return None

        doc = PersonaDocument(
            persona_id=persona_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            chunk_count=chunk_count,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        logger.info("persona_document_added", persona_id=str(persona_id), filename=filename)
        return doc

    def get_persona_documents(
        self, persona_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[PersonaDocument]:
        """Get all documents for a persona."""
        # Verify ownership
        persona = (
            self.db.query(Persona)
            .filter(Persona.id == persona_id, Persona.user_id == user_id)
            .first()
        )
        if not persona:
            return []

        return (
            self.db.query(PersonaDocument)
            .filter(PersonaDocument.persona_id == persona_id)
            .order_by(PersonaDocument.created_at.desc())
            .all()
        )

    def delete_document(
        self, doc_id: uuid.UUID, persona_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Delete a document from a persona."""
        # Verify ownership
        persona = (
            self.db.query(Persona)
            .filter(Persona.id == persona_id, Persona.user_id == user_id)
            .first()
        )
        if not persona:
            return False

        doc = (
            self.db.query(PersonaDocument)
            .filter(PersonaDocument.id == doc_id, PersonaDocument.persona_id == persona_id)
            .first()
        )
        if not doc:
            return False

        # Delete file from disk
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception as e:
                logger.warning("failed_to_delete_document_file", error=str(e))

        self.db.delete(doc)
        self.db.commit()

        logger.info("persona_document_deleted", doc_id=str(doc_id))
        return True

    def get_or_create_chat(
        self, persona_id: uuid.UUID, session_id: Optional[str] = None, visitor_name: Optional[str] = None
    ) -> PersonaChat:
        """Get or create a chat session for a persona."""
        if session_id:
            chat = (
                self.db.query(PersonaChat)
                .filter(
                    PersonaChat.persona_id == persona_id,
                    PersonaChat.visitor_session == session_id,
                )
                .first()
            )
            if chat:
                if visitor_name and not chat.visitor_name:
                    chat.visitor_name = visitor_name
                    self.db.commit()
                return chat

        # Create new chat
        new_session_id = session_id or secrets.token_urlsafe(32)
        chat = PersonaChat(
            persona_id=persona_id,
            visitor_session=new_session_id,
            visitor_name=visitor_name,
        )
        self.db.add(chat)

        # Increment persona chat count
        persona = self.db.query(Persona).filter(Persona.id == persona_id).first()
        if persona:
            persona.total_chats = (persona.total_chats or 0) + 1

        self.db.commit()
        self.db.refresh(chat)
        return chat

    def add_chat_message(
        self, chat_id: uuid.UUID, role: str, content: str
    ) -> PersonaChatMessage:
        """Add a message to a chat."""
        message = PersonaChatMessage(
            chat_id=chat_id,
            role=role,
            content=content,
        )
        self.db.add(message)

        # Update chat timestamp
        chat = self.db.query(PersonaChat).filter(PersonaChat.id == chat_id).first()
        if chat:
            chat.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(message)
        return message

    def get_chat_history(self, chat_id: uuid.UUID, limit: int = 50) -> List[PersonaChatMessage]:
        """Get chat history for a session."""
        return (
            self.db.query(PersonaChatMessage)
            .filter(PersonaChatMessage.chat_id == chat_id)
            .order_by(PersonaChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )

    def get_chat_by_session(
        self, persona_id: uuid.UUID, session_id: str
    ) -> Optional[PersonaChat]:
        """Get chat by session ID."""
        return (
            self.db.query(PersonaChat)
            .filter(
                PersonaChat.persona_id == persona_id,
                PersonaChat.visitor_session == session_id,
            )
            .first()
        )
