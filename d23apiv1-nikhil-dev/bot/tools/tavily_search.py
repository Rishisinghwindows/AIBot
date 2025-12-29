"""
Tavily Search Tool

Wrapper for Tavily API for local search functionality.
"""

from typing import Optional, Union
from bot.config import settings
from bot.state import ToolResult
from tavily import TavilyClient, AsyncTavilyClient

def _make_search_request(
    query: str,
    max_results: int = 5,
    include_answer: bool = True,
    client: Optional[Union[TavilyClient, AsyncTavilyClient]] = None,
) -> ToolResult:
    """
    Search for local places and businesses.

    Args:
        query: Search query (e.g., "restaurants near Connaught Place Delhi")
        max_results: Maximum number of results (default 5)
        include_answer: Include AI-generated answer summary
        client: Optional TavilyClient or AsyncTavilyClient instance

    Returns:
        ToolResult with search results or error
    """
    if not settings.TAVILY_API_KEY:
        return ToolResult(
            success=False,
            data=None,
            error="Tavily API key not configured",
            tool_name="tavily_search",
        )

    try:
        if client:
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer=include_answer,
                topic="general",
            )
        else:
            client = TavilyClient(api_key=settings.TAVILY_API_KEY)
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer=include_answer,
                topic="general",
            )

        return ToolResult(
            success=True,
            data={
                "query": response.get("query", query),
                "answer": response.get("answer"),
                "results": response.get("results", []),
                "response_time": response.get("response_time"),
            },
            error=None,
            tool_name="tavily_search",
        )

    except ImportError:
        return ToolResult(
            success=False,
            data=None,
            error="tavily-python package not installed",
            tool_name="tavily_search",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=f"Tavily search failed for query '{query}': {e}",
            tool_name="tavily_search",
        )


def search_local(
    query: str, max_results: int = 5, include_answer: bool = True
) -> ToolResult:
    """
    Search for local places and businesses.

    Args:
        query: Search query (e.g., "restaurants near Connaught Place Delhi")
        max_results: Maximum number of results (default 5)
        include_answer: Include AI-generated answer summary

    Returns:
        ToolResult with search results or error
    """
    return _make_search_request(
        query=query,
        max_results=max_results,
        include_answer=include_answer,
    )


async def search_local_async(
    query: str, max_results: int = 5, include_answer: bool = True
) -> ToolResult:
    """
    Async version of search_local.

    Args:
        query: Search query
        max_results: Maximum number of results
        include_answer: Include AI-generated answer summary

    Returns:
        ToolResult with search results or error
    """
    try:
        client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
        return await _make_search_request(
            query=query,
            max_results=max_results,
            include_answer=include_answer,
            client=client,
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=f"Tavily search failed for query '{query}': {e}",
            tool_name="tavily_search",
        )
