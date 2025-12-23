from __future__ import annotations

from typing import List, Optional, Dict, Any

import httpx

from app.interfaces import NotionSettingsProtocol
from app.logger import logger


class NotionService:
    """
    Notion API client for searching and managing pages and databases.
    Uses Integration Token for authentication.

    Accepts any settings object that implements NotionSettingsProtocol,
    allowing both app-level Settings and user-specific UserToolSettings.
    """

    def __init__(self, settings: NotionSettingsProtocol):
        self.api_key = getattr(settings, "notion_api_key", "")
        self.base_url = "https://api.notion.com/v1"
        self.available = bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Create auth headers for Notion API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    async def search(
        self,
        query: str,
        filter_type: Optional[str] = None,
        max_results: int = 10,
    ) -> str:
        """Search for pages and databases in Notion."""
        if not self.available:
            return "Notion is not configured. Please add your Notion API key in Settings > Integrations."

        try:
            payload: Dict[str, Any] = {
                "query": query,
                "page_size": max_results,
            }

            if filter_type in ("page", "database"):
                payload["filter"] = {"property": "object", "value": filter_type}

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/search",
                    headers=self._get_headers(),
                    json=payload,
                )

                if resp.status_code != 200:
                    return f"Notion API error: {resp.status_code} - {resp.text}"

                data = resp.json()
                results = data.get("results", [])

                if not results:
                    return f"No results found for: {query}"

                output = []
                for item in results:
                    obj_type = item.get("object", "unknown")
                    item_id = item.get("id", "")

                    if obj_type == "page":
                        title = self._extract_page_title(item)
                        url = item.get("url", "")
                        output.append(f"- [Page] {title}\n  URL: {url}")

                    elif obj_type == "database":
                        title = self._extract_database_title(item)
                        url = item.get("url", "")
                        output.append(f"- [Database] {title}\n  URL: {url}")

                return f"Found {len(results)} results:\n\n" + "\n\n".join(output)

        except Exception as exc:
            logger.error("notion_search_error", error=str(exc))
            return f"Notion error: {exc}"

    async def get_page(self, page_id: str) -> str:
        """Get details of a specific page."""
        if not self.available:
            return "Notion is not configured."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get page metadata
                resp = await client.get(
                    f"{self.base_url}/pages/{page_id}",
                    headers=self._get_headers(),
                )

                if resp.status_code != 200:
                    return f"Page not found: {resp.status_code}"

                page = resp.json()
                title = self._extract_page_title(page)
                url = page.get("url", "")
                created = page.get("created_time", "")[:10]
                updated = page.get("last_edited_time", "")[:10]

                # Get page content
                content_resp = await client.get(
                    f"{self.base_url}/blocks/{page_id}/children",
                    headers=self._get_headers(),
                    params={"page_size": 50},
                )

                content_text = ""
                if content_resp.status_code == 200:
                    blocks = content_resp.json().get("results", [])
                    content_text = self._extract_blocks_text(blocks)

                return (
                    f"Page: {title}\n"
                    f"URL: {url}\n"
                    f"Created: {created} | Updated: {updated}\n\n"
                    f"Content:\n{content_text[:2000]}"
                )

        except Exception as exc:
            logger.error("notion_get_page_error", error=str(exc))
            return f"Notion error: {exc}"

    async def create_page(
        self,
        parent_id: str,
        title: str,
        content: str,
        is_database: bool = False,
    ) -> str:
        """Create a new page in Notion."""
        if not self.available:
            return "Notion is not configured. Please add your Notion API key in Settings > Integrations."

        try:
            # Build parent reference
            if is_database:
                parent = {"database_id": parent_id}
                properties = {
                    "Name": {
                        "title": [{"text": {"content": title}}]
                    }
                }
            else:
                parent = {"page_id": parent_id}
                properties = {
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                }

            # Build content blocks
            children = []
            for paragraph in content.split("\n\n"):
                if paragraph.strip():
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": paragraph.strip()}}]
                        }
                    })

            payload = {
                "parent": parent,
                "properties": properties,
                "children": children,
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/pages",
                    headers=self._get_headers(),
                    json=payload,
                )

                if resp.status_code != 200:
                    error_data = resp.json()
                    return f"Failed to create page: {error_data.get('message', resp.text)}"

                page = resp.json()
                page_url = page.get("url", "")

                return f"Created page: {title}\nURL: {page_url}"

        except Exception as exc:
            logger.error("notion_create_page_error", error=str(exc))
            return f"Notion error: {exc}"

    async def query_database(
        self,
        database_id: str,
        filter_property: Optional[str] = None,
        filter_value: Optional[str] = None,
        max_results: int = 10,
    ) -> str:
        """Query a Notion database."""
        if not self.available:
            return "Notion is not configured."

        try:
            payload: Dict[str, Any] = {
                "page_size": max_results,
            }

            # Add filter if provided
            if filter_property and filter_value:
                payload["filter"] = {
                    "property": filter_property,
                    "rich_text": {"contains": filter_value},
                }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/databases/{database_id}/query",
                    headers=self._get_headers(),
                    json=payload,
                )

                if resp.status_code != 200:
                    return f"Database query error: {resp.status_code} - {resp.text}"

                data = resp.json()
                results = data.get("results", [])

                if not results:
                    return "No items found in database."

                output = []
                for item in results:
                    title = self._extract_page_title(item)
                    url = item.get("url", "")
                    properties = item.get("properties", {})

                    # Get a few key properties
                    prop_summary = []
                    for prop_name, prop_val in list(properties.items())[:3]:
                        if prop_name.lower() != "name":
                            prop_text = self._extract_property_value(prop_val)
                            if prop_text:
                                prop_summary.append(f"{prop_name}: {prop_text}")

                    output.append(
                        f"- {title}\n"
                        f"  {' | '.join(prop_summary) if prop_summary else 'No properties'}\n"
                        f"  URL: {url}"
                    )

                return f"Found {len(results)} items:\n\n" + "\n\n".join(output)

        except Exception as exc:
            logger.error("notion_query_database_error", error=str(exc))
            return f"Notion error: {exc}"

    async def append_to_page(self, page_id: str, content: str) -> str:
        """Append content blocks to an existing page."""
        if not self.available:
            return "Notion is not configured."

        try:
            children = []
            for paragraph in content.split("\n\n"):
                if paragraph.strip():
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": paragraph.strip()}}]
                        }
                    })

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.patch(
                    f"{self.base_url}/blocks/{page_id}/children",
                    headers=self._get_headers(),
                    json={"children": children},
                )

                if resp.status_code != 200:
                    return f"Failed to append content: {resp.text}"

                return f"Content appended to page successfully."

        except Exception as exc:
            logger.error("notion_append_error", error=str(exc))
            return f"Notion error: {exc}"

    async def list_databases(self, max_results: int = 10) -> str:
        """List accessible databases."""
        if not self.available:
            return "Notion is not configured."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/search",
                    headers=self._get_headers(),
                    json={
                        "filter": {"property": "object", "value": "database"},
                        "page_size": max_results,
                    },
                )

                if resp.status_code != 200:
                    return f"Notion API error: {resp.status_code}"

                data = resp.json()
                results = data.get("results", [])

                if not results:
                    return "No databases found."

                output = []
                for db in results:
                    title = self._extract_database_title(db)
                    db_id = db.get("id", "")
                    url = db.get("url", "")
                    output.append(f"- {title}\n  ID: {db_id}\n  URL: {url}")

                return f"Found {len(results)} databases:\n\n" + "\n\n".join(output)

        except Exception as exc:
            logger.error("notion_list_databases_error", error=str(exc))
            return f"Notion error: {exc}"

    def _extract_page_title(self, page: Dict) -> str:
        """Extract title from page object."""
        properties = page.get("properties", {})

        # Try common title property names
        for key in ["Name", "Title", "title", "name"]:
            if key in properties:
                prop = properties[key]
                if "title" in prop:
                    titles = prop["title"]
                    if titles:
                        return titles[0].get("plain_text", "Untitled")

        # Fallback to first title-type property
        for prop_val in properties.values():
            if isinstance(prop_val, dict) and "title" in prop_val:
                titles = prop_val["title"]
                if titles:
                    return titles[0].get("plain_text", "Untitled")

        return "Untitled"

    def _extract_database_title(self, db: Dict) -> str:
        """Extract title from database object."""
        title_array = db.get("title", [])
        if title_array:
            return title_array[0].get("plain_text", "Untitled Database")
        return "Untitled Database"

    def _extract_blocks_text(self, blocks: List[Dict]) -> str:
        """Extract text content from blocks."""
        text_parts = []

        for block in blocks:
            block_type = block.get("type", "")

            if block_type == "paragraph":
                rich_text = block.get("paragraph", {}).get("rich_text", [])
                text = "".join(t.get("plain_text", "") for t in rich_text)
                if text:
                    text_parts.append(text)

            elif block_type == "heading_1":
                rich_text = block.get("heading_1", {}).get("rich_text", [])
                text = "".join(t.get("plain_text", "") for t in rich_text)
                if text:
                    text_parts.append(f"# {text}")

            elif block_type == "heading_2":
                rich_text = block.get("heading_2", {}).get("rich_text", [])
                text = "".join(t.get("plain_text", "") for t in rich_text)
                if text:
                    text_parts.append(f"## {text}")

            elif block_type == "heading_3":
                rich_text = block.get("heading_3", {}).get("rich_text", [])
                text = "".join(t.get("plain_text", "") for t in rich_text)
                if text:
                    text_parts.append(f"### {text}")

            elif block_type == "bulleted_list_item":
                rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
                text = "".join(t.get("plain_text", "") for t in rich_text)
                if text:
                    text_parts.append(f"• {text}")

            elif block_type == "numbered_list_item":
                rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
                text = "".join(t.get("plain_text", "") for t in rich_text)
                if text:
                    text_parts.append(f"1. {text}")

            elif block_type == "to_do":
                rich_text = block.get("to_do", {}).get("rich_text", [])
                checked = block.get("to_do", {}).get("checked", False)
                text = "".join(t.get("plain_text", "") for t in rich_text)
                if text:
                    checkbox = "[x]" if checked else "[ ]"
                    text_parts.append(f"{checkbox} {text}")

            elif block_type == "code":
                rich_text = block.get("code", {}).get("rich_text", [])
                text = "".join(t.get("plain_text", "") for t in rich_text)
                language = block.get("code", {}).get("language", "")
                if text:
                    text_parts.append(f"```{language}\n{text}\n```")

            elif block_type == "quote":
                rich_text = block.get("quote", {}).get("rich_text", [])
                text = "".join(t.get("plain_text", "") for t in rich_text)
                if text:
                    text_parts.append(f"> {text}")

            elif block_type == "divider":
                text_parts.append("---")

        return "\n\n".join(text_parts)

    def _extract_property_value(self, prop: Dict) -> str:
        """Extract value from a property object."""
        prop_type = prop.get("type", "")

        if prop_type == "rich_text":
            texts = prop.get("rich_text", [])
            return "".join(t.get("plain_text", "") for t in texts)

        elif prop_type == "title":
            titles = prop.get("title", [])
            return "".join(t.get("plain_text", "") for t in titles)

        elif prop_type == "number":
            return str(prop.get("number", ""))

        elif prop_type == "select":
            select = prop.get("select")
            return select.get("name", "") if select else ""

        elif prop_type == "multi_select":
            options = prop.get("multi_select", [])
            return ", ".join(o.get("name", "") for o in options)

        elif prop_type == "date":
            date = prop.get("date")
            if date:
                start = date.get("start", "")
                end = date.get("end", "")
                return f"{start}" + (f" - {end}" if end else "")
            return ""

        elif prop_type == "checkbox":
            return "Yes" if prop.get("checkbox") else "No"

        elif prop_type == "url":
            return prop.get("url", "")

        elif prop_type == "email":
            return prop.get("email", "")

        elif prop_type == "phone_number":
            return prop.get("phone_number", "")

        elif prop_type == "status":
            status = prop.get("status")
            return status.get("name", "") if status else ""

        return ""
