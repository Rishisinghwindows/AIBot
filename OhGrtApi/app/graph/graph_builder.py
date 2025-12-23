from __future__ import annotations

from typing import Any, Dict

from langgraph.graph import END, START, StateGraph
from langchain_core.prompts import ChatPromptTemplate

from app.config import Settings
from app.graph.gmail_agent import GmailAgent
from app.graph.pdf_rag_agent import PDFRagAgent
from app.graph.postgres_agent import PostgresAgent
from app.graph.router import RouterAgent
from app.graph.weather_agent import WeatherAgent
from app.logger import logger
from app.services.gmail_service import GmailService
from app.services.postgres_service import PostgresService
from app.services.rag_service import RAGService
from app.services.weather_service import WeatherService
from app.utils.llm import build_chat_llm
from app.utils.models import AgentState, RouterCategory


class GraphBuilder:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = build_chat_llm(settings)
        self.router_agent = RouterAgent(self.llm)
        self.weather_agent = WeatherAgent(WeatherService(settings))
        self.pdf_agent = PDFRagAgent(RAGService(settings), self.llm)
        self.sql_agent = PostgresAgent(PostgresService(settings))
        self.gmail_agent = GmailAgent(GmailService(settings), self.llm)
        self.chat_prompt = ChatPromptTemplate.from_template(
            "You are a helpful assistant. Answer the user briefly.\nUser: {message}"
        )

    async def router_node(self, state: AgentState) -> Dict[str, Any]:
        category = await self.router_agent.route(state["message"])
        route_log = list(state.get("route_log", [])) + [category.value]
        return {"category": category.value, "route_log": route_log}

    async def _make_chat_response(self, message: str) -> str:
        messages = self.chat_prompt.format_messages(message=message)
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as exc:  # noqa: BLE001
            logger.error(f"chat_llm_error: {exc}")
            return "LLM unavailable. Please try again later."

    async def weather_node(self, state: AgentState) -> Dict[str, Any]:
        result = await self.weather_agent.run(state["message"])
        return {"response": result}

    async def pdf_node(self, state: AgentState) -> Dict[str, Any]:
        result = await self.pdf_agent.run(state["message"])
        return {"response": result}

    async def sql_node(self, state: AgentState) -> Dict[str, Any]:
        result = await self.sql_agent.run(state["message"])
        return {"response": result}

    async def gmail_node(self, state: AgentState) -> Dict[str, Any]:
        result = await self.gmail_agent.run(state["message"])
        return {"response": result}

    async def chat_node(self, state: AgentState) -> Dict[str, Any]:
        return {"response": await self._make_chat_response(state["message"])}

    def route_after_router(self, state: AgentState) -> str:
        category = state.get("category", RouterCategory.chat.value)
        return category

    def build(self):
        graph = StateGraph(AgentState)
        graph.add_node("router", self.router_node)
        graph.add_node("weather", self.weather_node)
        graph.add_node("pdf", self.pdf_node)
        graph.add_node("sql", self.sql_node)
        graph.add_node("gmail", self.gmail_node)
        graph.add_node("chat", self.chat_node)

        graph.add_edge(START, "router")
        graph.add_conditional_edges(
            "router",
            self.route_after_router,
            {
                RouterCategory.weather.value: "weather",
                RouterCategory.pdf.value: "pdf",
                RouterCategory.sql.value: "sql",
                RouterCategory.gmail.value: "gmail",
                RouterCategory.chat.value: "chat",
            },
        )
        graph.add_edge("weather", END)
        graph.add_edge("pdf", END)
        graph.add_edge("sql", END)
        graph.add_edge("gmail", END)
        graph.add_edge("chat", END)

        logger.info(f"langgraph_initialized: nodes={list(graph.nodes.keys())}")
        return graph.compile()


def build_graph(settings: Settings):
    return GraphBuilder(settings).build()
