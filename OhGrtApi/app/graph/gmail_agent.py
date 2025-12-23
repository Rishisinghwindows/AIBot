from __future__ import annotations

from app.logger import logger
from app.services.gmail_service import GmailService


class GmailAgent:
    def __init__(self, service: GmailService, llm):
        self.service = service
        self.llm = llm

    async def run(self, message: str) -> str:
        query = {"raw_query": message}
        try:
            emails = await self.service.search_emails(query)
        except Exception as exc:  # noqa: BLE001
            return (
                "Gmail is not ready. Please place your credentials.json, authorize once "
                "to generate token.json, then try again."
            )

        if not emails:
            return "No matching emails found."

        logger.info(f"gmail_agent_response: count={len(emails)}")
        summaries = [f"- {email.get('subject', 'No subject')}" for email in emails]
        return "Emails:\n" + "\n".join(summaries)
