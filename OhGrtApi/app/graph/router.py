from __future__ import annotations

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.logger import logger
from app.utils.models import RouterCategory


class RouterPrediction(BaseModel):
    category: RouterCategory = Field(description="One of: weather, pdf, sql, gmail, image, chat")


class RouterAgent:
    def __init__(self, llm):
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=RouterPrediction)
        self.prompt = ChatPromptTemplate.from_template(
            """You are a routing agent.
Classify the user request into exactly one of: [weather, pdf, sql, gmail, image, chat].

Categories:
- weather: Weather queries (temperature, forecast, etc.)
- pdf: Document/PDF queries
- sql: Database queries
- gmail: Email related queries
- image: Image generation requests (create/generate/make image/picture/photo)
- chat: General conversation

Return JSON only in this format:
{format_instructions}

User request: {message}"""
        )

    async def route(self, message: str) -> RouterCategory:
        messages = self.prompt.format_messages(
            message=message,
            format_instructions=self.parser.get_format_instructions(),
        )
        try:
            result = await self.llm.ainvoke(messages)
            parsed = self.parser.parse(result.content)
            category = parsed.category.value
        except Exception as exc:  # noqa: BLE001
            logger.error(f"router_llm_error: {exc}")
            # Fallback: keyword routing if LLM or parsing fails.
            text = message.lower()
            if any(w in text for w in ["weather", "temperature", "forecast"]):
                return RouterCategory.weather
            if "pdf" in text or "document" in text:
                return RouterCategory.pdf
            if any(w in text for w in ["sql", "database", "query"]):
                return RouterCategory.sql
            if "gmail" in text or "email" in text or "inbox" in text:
                return RouterCategory.gmail
            if any(w in text for w in ["generate image", "create image", "make image", "draw", "picture of", "photo of", "generate a", "create a picture"]):
                return RouterCategory.image
            return RouterCategory.chat

        logger.info(f"router_classification: category={category}")
        try:
            return RouterCategory(category)
        except ValueError:
            return RouterCategory.chat
