from __future__ import annotations

from typing import Dict, Any, Tuple, Optional

from ohgrt_api.logger import logger
from ohgrt_api.services.gmail_service import GmailService


class GmailAgent:
    def __init__(self, service: GmailService, llm):
        self.service = service
        self.llm = llm

    async def run(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Search emails and return both text response and structured data.

        Returns:
            Tuple of (text_response, structured_data)
            structured_data contains email list with IDs for clickable display
        """
        query = {"raw_query": message}
        try:
            emails = await self.service.search_emails(query)
        except Exception as exc:  # noqa: BLE001
            logger.error("gmail_agent_search_error", error=str(exc))
            return (
                "Gmail query failed. Please ensure Gmail is connected via Settings > Integrations. "
                f"Error: {str(exc)}",
                None
            )

        if not emails:
            return "No matching emails found.", None

        logger.info(f"gmail_agent_response: count={len(emails)}")

        # Build text response
        summaries = [f"- {email.get('subject', 'No subject')}" for email in emails]
        text_response = "Emails:\n" + "\n".join(summaries)

        # Build structured data for clickable email list
        structured_data = {
            "type": "email_list",
            "emails": [
                {
                    "id": email.get("id"),
                    "subject": email.get("subject", "No subject"),
                    "from": email.get("from", ""),
                    "date": email.get("date", ""),
                    "snippet": email.get("snippet", ""),
                }
                for email in emails
            ],
            "count": len(emails),
        }

        return text_response, structured_data
