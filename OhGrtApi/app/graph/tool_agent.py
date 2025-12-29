from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.services.confluence_service import ConfluenceService
from app.services.github_service import GitHubService
from app.services.gmail_service import GmailService
from app.services.drive_service import GoogleDriveService
from app.services.jira_service import JiraService
from app.services.postgres_service import PostgresService
from app.services.rag_service import RAGService
from app.services.custom_mcp_service import CustomMCPService
from app.services.slack_service import SlackService
from app.services.uber_service import UberService
from app.services.weather_service import WeatherService
from app.services.web_crawl_service import WebCrawlService
from app.services.astrology_service import get_astrology_service
from app.services.travel_service import get_travel_service
from app.services.news_service import get_news_service
from app.services.schedule_parser import parse_schedule, extract_task_from_message
from app.graph.nodes.image_node import generate_image_fal, _clean_prompt
from app.utils.llm import build_chat_llm
from app.utils.models import RouterCategory
from app.logger import logger


class ToolAgent:
    """Wrapper around LangGraph agent providing tool listing and per-request selection."""

    def __init__(
        self,
        settings,
        credentials: Dict[str, Any] | None = None,
        db=None,
        user_id: Optional[UUID] = None,
    ):
        self.settings = settings
        self.credentials = credentials or {}
        self.db = db
        self.user_id = user_id
        self.llm = build_chat_llm(settings)
        self.weather_service = WeatherService(settings)
        self.rag_service = RAGService(settings)

        # PostgresService is optional - skip if database not available
        try:
            self.sql_service = PostgresService(settings)
        except Exception:
            self.sql_service = None

        self.gmail_service = GmailService(settings, credential=self.credentials.get("gmail"))
        self.drive_service = GoogleDriveService(settings, credential=self.credentials.get("google_drive"))

        slack_token = self.credentials.get("slack", {}).get("access_token")
        self.slack_service = SlackService(settings, token_override=slack_token)

        conf_creds = self.credentials.get("confluence", {})
        self.confluence_service = ConfluenceService(
            settings,
            base_url_override=conf_creds.get("config", {}).get("base_url"),
            user_override=conf_creds.get("config", {}).get("user"),
            token_override=conf_creds.get("access_token"),
        )

        jira_creds = self.credentials.get("jira", {})
        self.jira_service = JiraService(
            settings,
            base_url=jira_creds.get("config", {}).get("base_url"),
            email=jira_creds.get("config", {}).get("user"),
            token=jira_creds.get("access_token"),
            project_key=jira_creds.get("config", {}).get("project_key"),
        )

        self.web_crawl_service = WebCrawlService()
        mcp_creds = self.credentials.get("custom_mcp", {})
        self.custom_mcp_service = CustomMCPService(
            base_url=mcp_creds.get("config", {}).get("base_url"),
            token=mcp_creds.get("access_token"),
        )
        github_creds = self.credentials.get("github", {})
        self.github_service = GitHubService(
            token=github_creds.get("access_token"),
            owner=github_creds.get("config", {}).get("owner"),
            repo=github_creds.get("config", {}).get("repo"),
        )

        # Uber service
        uber_creds = self.credentials.get("uber", {})
        self.uber_service = UberService(
            access_token=uber_creds.get("access_token"),
        )

        # D23Bot services
        self.astrology_service = get_astrology_service()
        railway_api_key = getattr(settings, "RAILWAY_API_KEY", None)
        self.travel_service = get_travel_service(railway_api_key)
        news_api_key = getattr(settings, "NEWS_API_KEY", None)
        self.news_service = get_news_service(news_api_key)

    def _build_tools(self):
        """Construct tool set and state for a single invocation."""
        last_tool: Dict[str, Any] = {"name": RouterCategory.chat.value, "structured_data": None}
        llm = self.llm

        @tool("weather", return_direct=True)
        async def weather_tool(city: str) -> str:
            """Get live weather for a city using OpenWeather."""
            last_tool["name"] = RouterCategory.weather.value
            weather = await self.weather_service.get_weather(city)
            # Store structured data for card rendering
            last_tool["structured_data"] = {
                "city": weather.city,
                "temperature": weather.temperature_c,
                "humidity": weather.humidity,
                "condition": weather.condition,
                "raw": weather.raw if hasattr(weather, 'raw') else {},
            }
            return (
                f"Weather for {weather.city}: {weather.temperature_c}°C, "
                f"humidity {weather.humidity}%, condition {weather.condition}."
            )

        @tool("pdf", return_direct=True)
        async def pdf_tool(question: str) -> str:
            """Answer a question using PDF RAG retrieval."""
            last_tool["name"] = RouterCategory.pdf.value
            from app.graph.pdf_rag_agent import PDFRagAgent

            pdf_agent = PDFRagAgent(self.rag_service, llm)
            try:
                return await pdf_agent.run(question)
            except Exception as exc:  # noqa: BLE001
                return (
                    "PDF search unavailable. Upload a PDF via /pdf/upload; "
                    "check that the Chroma store is writable. "
                    f"Details: {exc}"
                )

        @tool("sql", return_direct=True)
        async def sql_tool(question: str) -> str:
            """Convert a question to SQL and run it (read-only)."""
            last_tool["name"] = RouterCategory.sql.value
            if self.sql_service is None:
                return "SQL unavailable: Database not configured"
            try:
                return await asyncio.to_thread(self.sql_service.run_sql, question)
            except Exception as exc:  # noqa: BLE001
                return f"SQL unavailable: {exc}"

        @tool("gmail", return_direct=True)
        async def gmail_tool(query: str) -> str:
            """Search Gmail via MCP and summarize matches."""
            last_tool["name"] = RouterCategory.gmail.value
            from app.graph.gmail_agent import GmailAgent

            if not self.gmail_service.available:
                return "Gmail not configured. Per-user Gmail OAuth is not available in this build."

            gmail_agent = GmailAgent(self.gmail_service, llm)
            return await gmail_agent.run(query)

        @tool("google_drive_list", return_direct=True)
        async def google_drive_list_tool(query: str = "") -> str:
            """List Google Drive files (optional query)."""
            last_tool["name"] = "google_drive"
            try:
                files = await self.drive_service.list_files(query=query or None)
            except Exception as exc:  # noqa: BLE001
                return f"Google Drive unavailable: {exc}"
            if not files:
                return "No files found."
            lines = []
            for f in files:
                lines.append(f"- {f.get('name','(no name)')} ({f.get('mimeType','')})")
            return "Files:\n" + "\n".join(lines[:10])

        @tool("chat", return_direct=True)
        async def chat_tool(prompt: str) -> str:
            """General chat helper for non-tool questions."""
            last_tool["name"] = RouterCategory.chat.value
            try:
                resp = await llm.ainvoke([HumanMessage(content=prompt)])
                return resp.content
            except Exception:
                return "I can help with weather, PDFs, SQL, or Gmail. What would you like to do?"

        @tool("custom_mcp", return_direct=True)
        async def custom_mcp_tool(prompt: str) -> str:
            """Send a prompt to your configured custom MCP endpoint."""
            last_tool["name"] = "custom_mcp"
            return await self.custom_mcp_service.query(prompt)

        @tool("jira_search", return_direct=True)
        async def jira_search_tool(jql: str) -> str:
            """Search JIRA issues by JQL."""
            last_tool["name"] = "jira"
            return await self.jira_service.search(jql)

        @tool("jira_create", return_direct=True)
        async def jira_create_tool(summary: str, description: str) -> str:
            """Create a JIRA issue."""
            last_tool["name"] = "jira"
            return await self.jira_service.create_issue(summary, description)

        @tool("jira_add_watchers", return_direct=True)
        async def jira_add_watchers_tool(issue_key: str, emails: List[str]) -> str:
            """Add multiple watcher emails to a JIRA issue."""
            last_tool["name"] = "jira"
            return await self.jira_service.add_watchers(issue_key, emails)

        @tool("jira_remove_watcher", return_direct=True)
        async def jira_remove_watcher_tool(issue_key: str, email: str) -> str:
            """Remove a watcher email from a JIRA issue."""
            last_tool["name"] = "jira"
            return await self.jira_service.remove_watcher(issue_key, email)

        @tool("slack_post", return_direct=True)
        async def slack_post_tool(channel: str, text: str) -> str:
            """Post a message to a Slack channel."""
            last_tool["name"] = "slack"
            if not self.slack_service.available:
                return "Slack not configured. Set SLACK_TOKEN (and workspace settings) to enable."
            return await self.slack_service.post_message(channel, text)

        @tool("github_search", return_direct=True)
        async def github_search_tool(query: str) -> str:
            """Search GitHub issues in the configured repo."""
            last_tool["name"] = "github"
            return await self.github_service.search_issues(query)

        @tool("github_create", return_direct=True)
        async def github_create_tool(title: str, body: str) -> str:
            """Create a GitHub issue in the configured repo."""
            last_tool["name"] = "github"
            return await self.github_service.create_issue(title, body)

        @tool("github_commits", return_direct=True)
        async def github_commits_tool(limit: int = 10, branch: str = "") -> str:
            """List recent commits in the GitHub repo. Optional: limit (default 10), branch name."""
            last_tool["name"] = "github"
            return await self.github_service.list_commits(limit=limit, branch=branch)

        @tool("github_commit_detail", return_direct=True)
        async def github_commit_detail_tool(sha: str) -> str:
            """Get details of a specific commit by SHA hash."""
            last_tool["name"] = "github"
            return await self.github_service.get_commit(sha)

        @tool("github_prs", return_direct=True)
        async def github_prs_tool(state: str = "open", limit: int = 10) -> str:
            """List pull requests. State can be: open, closed, all. Default: open."""
            last_tool["name"] = "github"
            return await self.github_service.list_pull_requests(state=state, limit=limit)

        @tool("github_pr_detail", return_direct=True)
        async def github_pr_detail_tool(pr_number: int) -> str:
            """Get details of a specific pull request by number."""
            last_tool["name"] = "github"
            return await self.github_service.get_pull_request(pr_number)

        @tool("github_repo_info", return_direct=True)
        async def github_repo_info_tool() -> str:
            """Get repository information (stars, forks, description, etc.)."""
            last_tool["name"] = "github"
            return await self.github_service.get_repo_info()

        @tool("github_branches", return_direct=True)
        async def github_branches_tool(limit: int = 10) -> str:
            """List branches in the repository."""
            last_tool["name"] = "github"
            return await self.github_service.list_branches(limit=limit)

        @tool("github_contributors", return_direct=True)
        async def github_contributors_tool(limit: int = 10) -> str:
            """List top contributors to the repository."""
            last_tool["name"] = "github"
            return await self.github_service.list_contributors(limit=limit)

        @tool("github_file", return_direct=True)
        async def github_file_tool(path: str, branch: str = "") -> str:
            """Read a file from the repository. Provide file path (e.g., 'README.md')."""
            last_tool["name"] = "github"
            return await self.github_service.get_file_content(path=path, branch=branch)

        @tool("confluence_search", return_direct=True)
        async def confluence_search_tool(query: str) -> str:
            """Search Confluence pages by CQL query."""
            last_tool["name"] = "confluence"
            if not self.confluence_service.available:
                return "Confluence not configured. Set base URL/user/API token in .env to enable."
            return await self.confluence_service.search(query)

        @tool("web_crawl", return_direct=True)
        async def web_crawl_tool(url: str) -> str:
            """Fetch page text from a URL (first ~800 chars)."""
            last_tool["name"] = "crawl"
            try:
                content = await self.web_crawl_service.fetch(url)
                return f"Snippet from {url}:\n{content}"
            except Exception as exc:  # noqa: BLE001
                return f"Web crawl failed: {exc}"

        # ==================== D23Bot ASTROLOGY TOOLS ====================

        @tool("horoscope", return_direct=True)
        async def horoscope_tool(sign: str, period: str = "today") -> str:
            """Get daily/weekly/monthly horoscope for a zodiac sign. Period can be: today, tomorrow, weekly, monthly."""
            last_tool["name"] = "horoscope"
            result = await self.astrology_service.get_horoscope(sign, period)
            if result["success"]:
                data = result["data"]
                # Store structured data for card rendering
                last_tool["structured_data"] = {
                    "sign": data.get("sign"),
                    "zodiac_sign": data.get("sign"),
                    "period": data.get("period"),
                    "horoscope": data.get("horoscope"),
                    "daily_horoscope": data.get("horoscope"),
                    "lucky_number": data.get("lucky_number"),
                    "lucky_color": data.get("lucky_color"),
                    "advice": data.get("advice"),
                    "mood": data.get("mood"),
                    "compatibility": data.get("compatibility"),
                }
                return (
                    f"*{data['sign']} {data['period'].title()} Horoscope*\n\n"
                    f"{data['horoscope']}\n\n"
                    f"Lucky Number: {data['lucky_number']}\n"
                    f"Lucky Color: {data['lucky_color']}\n"
                    f"Advice: {data['advice']}"
                )
            return f"Could not get horoscope: {result.get('error', 'Unknown error')}"

        @tool("kundli", return_direct=True)
        async def kundli_tool(birth_date: str, birth_time: str, birth_place: str, name: str = "") -> str:
            """Generate birth chart (Kundli) from birth details. Date format: DD-MM-YYYY, Time format: HH:MM."""
            last_tool["name"] = "kundli"
            result = await self.astrology_service.calculate_kundli(birth_date, birth_time, birth_place, name or None)
            if result["success"]:
                data = result["data"]
                response = f"*Birth Chart (Kundli)*\n\n"
                if data.get('name'):
                    response += f"Name: {data['name']}\n"
                response += f"Birth: {data['birth_date']} at {data['birth_time']}\n"
                response += f"Place: {data['birth_place']}\n\n"
                response += f"Sun Sign: {data['sun_sign']}\n"
                response += f"Moon Sign: {data['moon_sign']}\n"
                response += f"Ascendant: {data['ascendant']['sign']}\n"
                response += f"Nakshatra: {data['moon_nakshatra']} (Pada {data['nakshatra_pada']})\n\n"
                response += f"Varna: {data['varna']} | Nadi: {data['nadi']} | Gana: {data['gana']}"
                return response
            return f"Could not generate kundli: {result.get('error', 'Unknown error')}"

        @tool("kundli_matching", return_direct=True)
        async def kundli_matching_tool(person1_dob: str, person2_dob: str, person1_name: str = "Person 1", person2_name: str = "Person 2") -> str:
            """Check marriage compatibility between two people using Ashtakoot Milan. DOB format: DD-MM-YYYY."""
            last_tool["name"] = "kundli_matching"
            result = await self.astrology_service.calculate_kundli_matching(
                person1_dob, person2_dob, person1_name, person2_name
            )
            if result["success"]:
                data = result["data"]
                response = f"*Kundli Matching Report*\n\n"
                response += f"{data['person1']['name']} ({data['person1']['moon_sign']}) & {data['person2']['name']} ({data['person2']['moon_sign']})\n\n"
                response += f"*Score: {data['total_score']}/36 ({data['percentage']}%)*\n"
                response += f"Verdict: {data['verdict']}\n\n"
                response += f"Recommendation: {data['recommendation']}"
                return response
            return f"Could not perform matching: {result.get('error', 'Unknown error')}"

        @tool("dosha_check", return_direct=True)
        async def dosha_check_tool(birth_date: str, birth_time: str, birth_place: str, dosha_type: str = "") -> str:
            """Check for doshas (Manglik, Kaal Sarp, Sade Sati, Pitra). Optional dosha_type: manglik, kaal_sarp, sade_sati, pitra."""
            last_tool["name"] = "dosha_check"
            result = await self.astrology_service.check_dosha(birth_date, birth_time, birth_place, dosha_type or None)
            if result["success"]:
                data = result["data"]
                response = "*Dosha Analysis*\n\n"
                for dosha_name, info in data["doshas"].items():
                    status = "Present" if info.get("present") or info.get("active") else "Not Present"
                    response += f"*{dosha_name.replace('_', ' ').title()}*: {status}\n"
                    response += f"  {info['description']}\n"
                    if info.get("remedy"):
                        response += f"  Remedy: {info['remedy']}\n"
                    response += "\n"
                return response
            return f"Could not check dosha: {result.get('error', 'Unknown error')}"

        @tool("life_prediction", return_direct=True)
        async def life_prediction_tool(birth_date: str, birth_time: str, birth_place: str, prediction_type: str = "general") -> str:
            """Get life predictions. Types: general, marriage, career, children, wealth, health, foreign."""
            last_tool["name"] = "life_prediction"
            result = await self.astrology_service.get_life_prediction(birth_date, birth_time, birth_place, prediction_type)
            if result["success"]:
                data = result["data"]
                if prediction_type == "general":
                    response = "*Life Predictions Overview*\n\n"
                    for pred_type, pred in data.get("predictions", {}).items():
                        response += f"*{pred['title']}*: See detailed analysis\n"
                else:
                    pred = data.get("prediction", {})
                    response = f"*{pred.get('title', 'Prediction')}*\n\n"
                    for key, value in pred.items():
                        if key != "title" and value:
                            response += f"{key.replace('_', ' ').title()}: {value}\n"
                return response
            return f"Could not get prediction: {result.get('error', 'Unknown error')}"

        @tool("panchang", return_direct=True)
        async def panchang_tool(date: str = "", place: str = "Delhi") -> str:
            """Get Panchang (Hindu calendar) for a date. Date format: DD-MM-YYYY. Defaults to today."""
            last_tool["name"] = "panchang"
            result = await self.astrology_service.get_panchang(date or None, place)
            if result["success"]:
                data = result["data"]
                response = f"*Panchang for {data['date']}*\n\n"
                response += f"Day: {data['day']}\n"
                response += f"Tithi: {data['tithi']['name']} ({data['tithi']['paksha']})\n"
                response += f"Nakshatra: {data['nakshatra']['name']} (Pada {data['nakshatra']['pada']})\n"
                response += f"Yoga: {data['yoga']}\n"
                response += f"Moon Sign: {data['moon_sign']}\n\n"
                response += f"Sunrise: {data['sunrise']} | Sunset: {data['sunset']}\n"
                response += f"Rahu Kaal: {data['rahu_kaal']}\n"
                response += f"Auspicious Time: {data['auspicious_time']}"
                return response
            return f"Could not get panchang: {result.get('error', 'Unknown error')}"

        @tool("numerology", return_direct=True)
        async def numerology_tool(name: str, birth_date: str = "") -> str:
            """Calculate numerology for a name. Optional birth_date (DD-MM-YYYY) for life path number."""
            last_tool["name"] = "numerology"
            result = await self.astrology_service.calculate_numerology(name, birth_date or None)
            if result["success"]:
                data = result["data"]
                # Store structured data for card rendering
                last_tool["structured_data"] = {
                    "name": data.get("name"),
                    "name_number": data.get("name_number"),
                    "name_meaning": data.get("name_meaning"),
                    "birth_date": data.get("birth_date"),
                    "life_path_number": data.get("life_path_number"),
                    "life_path_meaning": data.get("life_path_meaning"),
                    "lucky_numbers": data.get("lucky_numbers", []),
                    "expression_number": data.get("expression_number"),
                    "soul_urge_number": data.get("soul_urge_number"),
                    "personality_number": data.get("personality_number"),
                }
                response = f"*Numerology for {data['name']}*\n\n"
                response += f"Name Number: {data['name_number']}\n"
                meaning = data.get('name_meaning', {})
                response += f"Trait: {meaning.get('trait', 'N/A')}\n"
                response += f"Description: {meaning.get('description', 'N/A')}\n"
                if data.get('life_path_number'):
                    response += f"\nLife Path Number: {data['life_path_number']}\n"
                    lp_meaning = data.get('life_path_meaning', {})
                    response += f"Life Path Trait: {lp_meaning.get('trait', 'N/A')}\n"
                response += f"\nLucky Numbers: {', '.join(map(str, data.get('lucky_numbers', [])))}"
                return response
            return f"Could not calculate numerology: {result.get('error', 'Unknown error')}"

        @tool("tarot", return_direct=True)
        async def tarot_tool(question: str = "", spread_type: str = "three_card") -> str:
            """Draw tarot cards. Spread types: single, three_card, celtic_cross."""
            last_tool["name"] = "tarot"
            result = await self.astrology_service.draw_tarot(question or None, spread_type)
            if result["success"]:
                data = result["data"]
                # Store structured data for card rendering
                last_tool["structured_data"] = {
                    "spread_type": data.get("spread_type"),
                    "question": data.get("question"),
                    "cards": data.get("cards", []),
                    "interpretation": data.get("interpretation"),
                }
                response = f"*Tarot Reading ({data['spread_type'].replace('_', ' ').title()})*\n\n"
                if data.get('question'):
                    response += f"Question: {data['question']}\n\n"
                response += "*Cards Drawn:*\n"
                for card in data['cards']:
                    orientation = "(Reversed)" if card['reversed'] else "(Upright)"
                    response += f"- {card['position']}: {card['card']} {orientation}\n"
                response += f"\n*Interpretation:*\n{data['interpretation']}"
                return response
            return f"Could not draw tarot: {result.get('error', 'Unknown error')}"

        @tool("ask_astrologer", return_direct=True)
        async def ask_astrologer_tool(question: str, user_sign: str = "") -> str:
            """Ask any astrology question. Optionally provide your zodiac sign."""
            last_tool["name"] = "ask_astrologer"
            result = await self.astrology_service.ask_astrologer(question, user_sign or None)
            if result["success"]:
                data = result["data"]
                return f"*Astrologer's Answer*\n\n{data['answer']}"
            return f"Could not answer: {result.get('error', 'Unknown error')}"

        # ==================== D23Bot TRAVEL TOOLS ====================

        @tool("pnr_status", return_direct=True)
        async def pnr_status_tool(pnr: str) -> str:
            """Check Indian Railways PNR status. Provide 10-digit PNR number."""
            last_tool["name"] = "pnr_status"
            result = await self.travel_service.get_pnr_status(pnr)
            if result["success"]:
                data = result["data"]
                # Store structured data for card rendering
                last_tool["structured_data"] = {
                    "pnr": data.get("pnr"),
                    "train_number": data.get("train_number"),
                    "train_name": data.get("train_name"),
                    "from_station": data.get("from_station"),
                    "to_station": data.get("to_station"),
                    "journey_date": data.get("journey_date"),
                    "class": data.get("class"),
                    "chart_prepared": data.get("chart_prepared"),
                    "passengers": data.get("passengers", []),
                }
                response = f"*PNR Status: {data['pnr']}*\n\n"
                response += f"Train: {data['train_name']} ({data['train_number']})\n"
                response += f"From: {data['from_station']}\n"
                response += f"To: {data['to_station']}\n"
                response += f"Date: {data['journey_date']}\n"
                response += f"Class: {data['class']}\n"
                response += f"Chart: {'Prepared' if data['chart_prepared'] else 'Not Prepared'}\n\n"
                response += "*Passengers:*\n"
                for i, p in enumerate(data['passengers'], 1):
                    response += f"{i}. {p['current_status']}\n"
                return response
            return f"Could not get PNR status: {result.get('error', 'Unknown error')}"

        @tool("train_status", return_direct=True)
        async def train_status_tool(train_number: str, date: str = "") -> str:
            """Check live train running status. Provide train number (4-5 digits)."""
            last_tool["name"] = "train_status"
            result = await self.travel_service.get_train_status(train_number, date or None)
            if result["success"]:
                data = result["data"]
                delay = data['delay_minutes']
                delay_text = "On Time" if delay == 0 else f"Late by {delay} min" if delay > 0 else f"Early by {abs(delay)} min"
                response = f"*Train: {data['train_name']}* ({data['train_number']})\n\n"
                response += f"Status: {data['running_status']}\n"
                response += f"Delay: {delay_text}\n\n"
                if data.get('last_station'):
                    response += f"Last Station: {data['last_station']} ({data.get('last_station_time', '')})\n"
                if data.get('next_station'):
                    response += f"Next Station: {data['next_station']} (ETA: {data.get('eta_next_station', '')})"
                return response
            return f"Could not get train status: {result.get('error', 'Unknown error')}"

        @tool("metro_info", return_direct=True)
        async def metro_info_tool(source: str, destination: str, city: str = "delhi") -> str:
            """Get metro route and fare information between stations."""
            last_tool["name"] = "metro_info"
            result = await self.travel_service.get_metro_info(source, destination, city)
            if result["success"]:
                data = result["data"]
                response = f"*Metro Route: {data['source']} to {data['destination']}*\n\n"
                response += f"Distance: {data['distance_km']} km\n"
                response += f"Time: ~{data['time_minutes']} minutes\n"
                response += f"Fare: ₹{data['fare']}\n"
                response += f"Interchanges: {data['interchanges']}\n"
                if data.get('interchange_stations'):
                    response += f"Change at: {', '.join(data['interchange_stations'])}\n"
                response += f"\nFirst Train: {data['first_train']} | Last Train: {data['last_train']}"
                return response
            return f"Could not get metro info: {result.get('error', 'Unknown error')}"

        # ==================== D23Bot NEWS TOOL ====================

        @tool("news", return_direct=True)
        async def news_tool(query: str = "", category: str = "") -> str:
            """Get latest news headlines. Optional query for search, category: business, sports, technology, entertainment."""
            last_tool["name"] = "news"
            result = await self.news_service.get_news(query or None, category or None, limit=5)
            if result["success"]:
                data = result["data"]
                # Store structured data for card rendering
                last_tool["structured_data"] = {
                    "articles": data.get("articles", []),
                    "items": data.get("articles", []),
                    "query": data.get("query"),
                    "category": data.get("category"),
                }
                response = "*Latest News*\n"
                if data.get('query'):
                    response += f"(Search: {data['query']})\n"
                if data.get('category'):
                    response += f"(Category: {data['category']})\n"
                response += "\n"
                for i, article in enumerate(data['articles'], 1):
                    response += f"{i}. *{article['title']}*\n"
                    if article.get('description'):
                        response += f"   {article['description'][:100]}...\n"
                    response += f"   Source: {article['source']}\n\n"
                return response
            return f"Could not get news: {result.get('error', 'Unknown error')}"

        # ==================== IMAGE GENERATION TOOL ====================

        @tool("image_gen", return_direct=True)
        async def image_gen_tool(prompt: str) -> str:
            """Generate an AI image from a text description. Describe what you want to see."""
            last_tool["name"] = "image_gen"
            clean_prompt = _clean_prompt(prompt)
            result = await generate_image_fal(clean_prompt)
            if result.get("success"):
                image_url = result.get("data", {}).get("image_url")
                if image_url:
                    last_tool["media_url"] = image_url
                    last_tool["structured_data"] = {
                        "prompt": clean_prompt,
                        "image_url": image_url,
                    }
                    # Return just the prompt description - image displays via media_url
                    return f"Here's the generated image for: {clean_prompt}"
            error = result.get("error", "Unknown error")
            return f"Could not generate image: {error}"

        # ==================== UBER TOOLS ====================

        @tool("uber_profile", return_direct=True)
        async def uber_profile_tool() -> str:
            """Get your Uber profile information."""
            last_tool["name"] = "uber"
            if not self.uber_service.available:
                return "Uber not connected. Connect via Settings > Integrations > Uber."
            result = await self.uber_service.get_profile()
            if result["success"]:
                data = result["data"]
                return (
                    f"*Uber Profile*\n\n"
                    f"Name: {data.get('first_name', '')} {data.get('last_name', '')}\n"
                    f"Email: {data.get('email', 'N/A')}"
                )
            return f"Could not get Uber profile: {result.get('error', 'Unknown error')}"

        @tool("uber_history", return_direct=True)
        async def uber_history_tool(limit: int = 5) -> str:
            """Get your recent Uber ride history. Optional limit (default 5, max 50)."""
            last_tool["name"] = "uber"
            if not self.uber_service.available:
                return "Uber not connected. Connect via Settings > Integrations > Uber."
            result = await self.uber_service.get_ride_history(limit=min(limit, 50))
            if result["success"]:
                data = result["data"]
                rides = data.get("rides", [])
                if not rides:
                    return "*Uber Ride History*\n\nNo rides found."
                response = f"*Uber Ride History* ({len(rides)} rides)\n\n"
                for i, ride in enumerate(rides, 1):
                    response += f"{i}. {ride.get('start_city', 'Unknown')}\n"
                    response += f"   Status: {ride.get('status', 'N/A')}\n"
                    if ride.get('distance'):
                        response += f"   Distance: {ride['distance']:.1f} miles\n"
                    response += "\n"
                return response
            return f"Could not get ride history: {result.get('error', 'Unknown error')}"

        @tool("uber_price", return_direct=True)
        async def uber_price_tool(start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> str:
            """Get Uber price estimates between two locations. Provide coordinates."""
            last_tool["name"] = "uber"
            if not self.uber_service.available:
                return "Uber not connected. Connect via Settings > Integrations > Uber."
            result = await self.uber_service.get_price_estimate(start_lat, start_lng, end_lat, end_lng)
            if result["success"]:
                data = result["data"]
                estimates = data.get("estimates", [])
                if not estimates:
                    return "*Uber Price Estimates*\n\nNo estimates available for this route."
                response = "*Uber Price Estimates*\n\n"
                for est in estimates:
                    surge = ""
                    if est.get('surge_multiplier', 1.0) > 1.0:
                        surge = f" (Surge: {est['surge_multiplier']}x)"
                    response += f"*{est['product_name']}*: {est.get('estimate', 'N/A')}{surge}\n"
                    if est.get('duration'):
                        mins = round(est['duration'] / 60)
                        response += f"   Duration: ~{mins} min | Distance: {est.get('distance', 'N/A')} mi\n"
                    response += "\n"
                return response
            return f"Could not get price estimates: {result.get('error', 'Unknown error')}"

        @tool("uber_eta", return_direct=True)
        async def uber_eta_tool(lat: float, lng: float) -> str:
            """Get Uber driver ETA at a location. Provide coordinates."""
            last_tool["name"] = "uber"
            if not self.uber_service.available:
                return "Uber not connected. Connect via Settings > Integrations > Uber."
            result = await self.uber_service.get_time_estimate(lat, lng)
            if result["success"]:
                data = result["data"]
                estimates = data.get("estimates", [])
                if not estimates:
                    return "*Uber ETA*\n\nNo drivers available at this location."
                response = "*Uber Driver ETA*\n\n"
                for est in estimates:
                    response += f"*{est['product_name']}*: {est['eta_minutes']} min\n"
                return response
            return f"Could not get ETA: {result.get('error', 'Unknown error')}"

        @tool("uber_products", return_direct=True)
        async def uber_products_tool(lat: float, lng: float) -> str:
            """Get available Uber products at a location. Provide coordinates."""
            last_tool["name"] = "uber"
            if not self.uber_service.available:
                return "Uber not connected. Connect via Settings > Integrations > Uber."
            result = await self.uber_service.get_products(lat, lng)
            if result["success"]:
                data = result["data"]
                products = data.get("products", [])
                if not products:
                    return "*Uber Products*\n\nNo Uber products available at this location."
                response = "*Available Uber Products*\n\n"
                for prod in products:
                    response += f"*{prod['name']}*"
                    if prod.get('capacity'):
                        response += f" (Seats: {prod['capacity']})"
                    response += "\n"
                    if prod.get('description'):
                        response += f"   {prod['description']}\n"
                return response
            return f"Could not get products: {result.get('error', 'Unknown error')}"

        # ==================== SCHEDULING TOOL ====================

        @tool("schedule_task", return_direct=True)
        async def schedule_task_tool(message: str) -> str:
            """Schedule a reminder, alert, or recurring task from natural language.
            Examples: 'remind me to check portfolio at 12 pm', 'schedule alert every day at 9am'."""
            last_tool["name"] = "schedule_task"

            # Parse the schedule from natural language
            parsed = parse_schedule(message)
            title, agent_prompt = extract_task_from_message(message)

            # Try to create the task via database
            try:
                from app.db.base import SessionLocal
                from app.tasks.service import ScheduledTaskService

                db = SessionLocal()
                try:
                    service = ScheduledTaskService(db)

                    # Use user_id from the ToolAgent instance (captured via closure)
                    task_user_id = self.user_id

                    if not task_user_id:
                        return "Please sign in to create scheduled tasks. Anonymous scheduling is not supported."

                    # Create the task
                    task = service.create_task(
                        title=title,
                        description=f"Created via chat: {message}",
                        task_type="scheduled_query" if agent_prompt else "reminder",
                        schedule_type=parsed.schedule_type,
                        user_id=task_user_id,
                        scheduled_at=parsed.scheduled_at,
                        cron_expression=parsed.cron_expression,
                        task_timezone="Asia/Kolkata",  # Default to IST for Indian users
                        agent_prompt=agent_prompt,
                        notify_via={"push": True},
                    )

                    # Format response
                    response = f"✅ *Scheduled Task Created*\n\n"
                    response += f"*Title:* {task.title}\n"
                    response += f"*Schedule:* {parsed.description}\n"
                    if task.next_run_at:
                        next_run_str = task.next_run_at.strftime("%d %b %Y at %I:%M %p")
                        response += f"*Next Run:* {next_run_str}\n"

                    if parsed.schedule_type == "cron":
                        response += f"\nThis will repeat {parsed.description.lower()}."
                    elif parsed.schedule_type == "one_time":
                        response += "\nThis is a one-time reminder."

                    response += "\n\nYou can view and manage your scheduled tasks in the Tasks section."

                    return response

                finally:
                    db.close()

            except Exception as e:
                return f"I understood you want to schedule: '{title}' ({parsed.description}), but couldn't create it: {str(e)}"

        @tool("list_tasks", return_direct=True)
        async def list_tasks_tool(status: str = "active") -> str:
            """List your scheduled tasks and reminders. Status can be: active, paused, completed, all."""
            last_tool["name"] = "list_tasks"

            try:
                from app.db.base import SessionLocal
                from app.tasks.service import ScheduledTaskService

                db = SessionLocal()
                try:
                    service = ScheduledTaskService(db)

                    # Get tasks for current user
                    status_filter = None if status == "all" else status
                    tasks, total, _ = service.get_tasks(
                        user_id=self.user_id,
                        status=status_filter,
                        limit=10,
                    )

                    if not tasks:
                        return f"You don't have any {status} scheduled tasks."

                    response = f"📋 *Your Scheduled Tasks* ({total} total)\n\n"
                    for i, task in enumerate(tasks, 1):
                        status_emoji = {"active": "🟢", "paused": "⏸️", "completed": "✅", "cancelled": "❌"}.get(task.status, "⚪")
                        response += f"{i}. {status_emoji} *{task.title}*\n"
                        response += f"   Type: {task.schedule_type} | Status: {task.status}\n"
                        if task.next_run_at:
                            next_run = task.next_run_at.strftime("%d %b %Y at %I:%M %p")
                            response += f"   Next run: {next_run}\n"
                        if task.description:
                            response += f"   Note: {task.description[:50]}...\n" if len(task.description) > 50 else f"   Note: {task.description}\n"
                        response += f"   ID: `{str(task.id)[:8]}`\n\n"

                    return response

                finally:
                    db.close()

            except Exception as e:
                logger.error("list_tasks_error", error=str(e))
                return f"Could not list tasks: {str(e)}"

        @tool("delete_task", return_direct=True)
        async def delete_task_tool(task_id: str) -> str:
            """Delete a scheduled task by its ID. Use list_tasks to find the task ID."""
            last_tool["name"] = "delete_task"

            try:
                from app.db.base import SessionLocal
                from app.tasks.service import ScheduledTaskService
                from uuid import UUID

                db = SessionLocal()
                try:
                    service = ScheduledTaskService(db)

                    # Try to parse UUID (support both full and short IDs)
                    try:
                        # First try full UUID
                        parsed_id = UUID(task_id)
                    except ValueError:
                        # Try to find task by partial ID
                        tasks, _, _ = service.get_tasks(user_id=self.user_id, limit=100)
                        matching = [t for t in tasks if str(t.id).startswith(task_id)]
                        if len(matching) == 1:
                            parsed_id = matching[0].id
                        elif len(matching) > 1:
                            return f"Multiple tasks match '{task_id}'. Please provide a more specific ID."
                        else:
                            return f"No task found with ID '{task_id}'. Use list_tasks to see your tasks."

                    # Get task title before deleting
                    task = service.get_task(parsed_id, user_id=self.user_id)
                    if not task:
                        return f"Task not found or you don't have permission to delete it."

                    task_title = task.title

                    # Delete the task
                    deleted = service.delete_task(parsed_id, user_id=self.user_id)

                    if deleted:
                        return f"✅ Deleted task: *{task_title}*"
                    else:
                        return f"Could not delete task. Make sure you have permission."

                finally:
                    db.close()

            except Exception as e:
                logger.error("delete_task_error", error=str(e))
                return f"Could not delete task: {str(e)}"

        @tool("pause_task", return_direct=True)
        async def pause_task_tool(task_id: str) -> str:
            """Pause a recurring scheduled task. The task won't run until resumed."""
            last_tool["name"] = "pause_task"

            try:
                from app.db.base import SessionLocal
                from app.tasks.service import ScheduledTaskService
                from uuid import UUID

                db = SessionLocal()
                try:
                    service = ScheduledTaskService(db)

                    # Parse task ID
                    try:
                        parsed_id = UUID(task_id)
                    except ValueError:
                        tasks, _, _ = service.get_tasks(user_id=self.user_id, limit=100)
                        matching = [t for t in tasks if str(t.id).startswith(task_id)]
                        if len(matching) == 1:
                            parsed_id = matching[0].id
                        elif len(matching) > 1:
                            return f"Multiple tasks match '{task_id}'. Please provide a more specific ID."
                        else:
                            return f"No task found with ID '{task_id}'."

                    task = service.pause_task(parsed_id, user_id=self.user_id)

                    if task:
                        return f"⏸️ Paused task: *{task.title}*\n\nUse 'resume task {task_id}' to resume it."
                    else:
                        return f"Could not pause task. It may already be paused or doesn't exist."

                finally:
                    db.close()

            except Exception as e:
                logger.error("pause_task_error", error=str(e))
                return f"Could not pause task: {str(e)}"

        @tool("resume_task", return_direct=True)
        async def resume_task_tool(task_id: str) -> str:
            """Resume a paused scheduled task."""
            last_tool["name"] = "resume_task"

            try:
                from app.db.base import SessionLocal
                from app.tasks.service import ScheduledTaskService
                from uuid import UUID

                db = SessionLocal()
                try:
                    service = ScheduledTaskService(db)

                    # Parse task ID
                    try:
                        parsed_id = UUID(task_id)
                    except ValueError:
                        tasks, _, _ = service.get_tasks(user_id=self.user_id, status="paused", limit=100)
                        matching = [t for t in tasks if str(t.id).startswith(task_id)]
                        if len(matching) == 1:
                            parsed_id = matching[0].id
                        elif len(matching) > 1:
                            return f"Multiple tasks match '{task_id}'. Please provide a more specific ID."
                        else:
                            return f"No paused task found with ID '{task_id}'."

                    task = service.resume_task(parsed_id, user_id=self.user_id)

                    if task:
                        next_run = task.next_run_at.strftime("%d %b %Y at %I:%M %p") if task.next_run_at else "soon"
                        return f"▶️ Resumed task: *{task.title}*\n\nNext run: {next_run}"
                    else:
                        return f"Could not resume task. It may not be paused or doesn't exist."

                finally:
                    db.close()

            except Exception as e:
                logger.error("resume_task_error", error=str(e))
                return f"Could not resume task: {str(e)}"

        @tool("update_task", return_direct=True)
        async def update_task_tool(task_id: str, title: str = "", description: str = "") -> str:
            """Update a scheduled task's title or description."""
            last_tool["name"] = "update_task"

            if not title and not description:
                return "Please provide a new title or description to update."

            try:
                from app.db.base import SessionLocal
                from app.tasks.service import ScheduledTaskService
                from uuid import UUID

                db = SessionLocal()
                try:
                    service = ScheduledTaskService(db)

                    # Parse task ID
                    try:
                        parsed_id = UUID(task_id)
                    except ValueError:
                        tasks, _, _ = service.get_tasks(user_id=self.user_id, limit=100)
                        matching = [t for t in tasks if str(t.id).startswith(task_id)]
                        if len(matching) == 1:
                            parsed_id = matching[0].id
                        elif len(matching) > 1:
                            return f"Multiple tasks match '{task_id}'. Please provide a more specific ID."
                        else:
                            return f"No task found with ID '{task_id}'."

                    # Build update kwargs
                    updates = {}
                    if title:
                        updates["title"] = title
                    if description:
                        updates["description"] = description

                    task = service.update_task(parsed_id, user_id=self.user_id, **updates)

                    if task:
                        return f"✏️ Updated task: *{task.title}*"
                    else:
                        return f"Could not update task. Make sure it exists and you have permission."

                finally:
                    db.close()

            except Exception as e:
                logger.error("update_task_error", error=str(e))
                return f"Could not update task: {str(e)}"

        tools = [
            weather_tool,
            pdf_tool,
            sql_tool,
            gmail_tool,
            google_drive_list_tool,
            jira_search_tool,
            jira_create_tool,
            jira_add_watchers_tool,
            jira_remove_watcher_tool,
            slack_post_tool,
            github_search_tool,
            github_create_tool,
            github_commits_tool,
            github_commit_detail_tool,
            github_prs_tool,
            github_pr_detail_tool,
            github_repo_info_tool,
            github_branches_tool,
            github_contributors_tool,
            github_file_tool,
            confluence_search_tool,
            custom_mcp_tool,
            web_crawl_tool,
            # D23Bot Astrology tools
            horoscope_tool,
            kundli_tool,
            kundli_matching_tool,
            dosha_check_tool,
            life_prediction_tool,
            panchang_tool,
            numerology_tool,
            tarot_tool,
            ask_astrologer_tool,
            # D23Bot Travel tools
            pnr_status_tool,
            train_status_tool,
            metro_info_tool,
            # D23Bot News tool
            news_tool,
            # Image generation tool
            image_gen_tool,
            # Uber tools
            uber_profile_tool,
            uber_history_tool,
            uber_price_tool,
            uber_eta_tool,
            uber_products_tool,
            # Scheduling tools
            schedule_task_tool,
            list_tasks_tool,
            delete_task_tool,
            pause_task_tool,
            resume_task_tool,
            update_task_tool,
            # General chat
            chat_tool,
        ]
        return tools, last_tool

    def list_tools(self) -> List[Dict[str, str]]:
        """Return tool metadata for UI."""
        tools, _ = self._build_tools()
        availability = {
            "slack_post": self.slack_service.available,
            "confluence_search": self.confluence_service.available,
            "jira_search": self.jira_service.available,
            "jira_create": self.jira_service.available and bool(self.jira_service.project_key),
            "jira_add_watchers": self.jira_service.available,
            "jira_remove_watcher": self.jira_service.available,
            "custom_mcp": self.custom_mcp_service.available,
            "gmail": self.gmail_service.available,
            "github_search": self.github_service.available,
            "github_create": self.github_service.available,
            "github_commits": self.github_service.available,
            "github_commit_detail": self.github_service.available,
            "github_prs": self.github_service.available,
            "github_pr_detail": self.github_service.available,
            "github_repo_info": self.github_service.available,
            "github_branches": self.github_service.available,
            "github_contributors": self.github_service.available,
            "github_file": self.github_service.available,
            "google_drive_list": self.drive_service.available,
            "uber_profile": self.uber_service.available,
            "uber_history": self.uber_service.available,
            "uber_price": self.uber_service.available,
            "uber_eta": self.uber_service.available,
            "uber_products": self.uber_service.available,
            # Task tools require user_id
            "list_tasks": self.user_id is not None,
            "delete_task": self.user_id is not None,
            "pause_task": self.user_id is not None,
            "resume_task": self.user_id is not None,
            "update_task": self.user_id is not None,
        }

        def is_available(name: str) -> bool:
            return availability.get(name, True)

        return [
            {
                "name": tool.name,
                "description": tool.description or "",
            }
            for tool in tools
            if is_available(tool.name)
        ]

    async def _get_mcp_tools(self) -> List[Any]:
        """
        Dynamically discover and load MCP tools from user's configured servers.

        Returns:
            List of LangChain tools from MCP servers
        """
        if not self.db or not self.user_id:
            return []

        try:
            from app.mcp.langchain_bridge import get_mcp_tools_for_user
            mcp_tools = await get_mcp_tools_for_user(self.db, self.user_id)
            logger.info("mcp_tools_loaded", count=len(mcp_tools), user_id=str(self.user_id))
            return mcp_tools
        except Exception as e:
            logger.warning("mcp_tools_load_failed", error=str(e))
            return []

    async def invoke(self, message: str, allowed_tools: List[str] | None = None) -> Dict[str, Any]:
        """
        Run the agent with an optional subset of tools.

        Dynamically loads MCP tools from user's configured servers and
        combines them with built-in tools.
        """
        tools, last_tool = self._build_tools()
        tool_map = {t.name: t for t in tools}

        # Dynamically load MCP tools from user's configured servers
        mcp_tools = await self._get_mcp_tools()
        if mcp_tools:
            tools.extend(mcp_tools)
            for t in mcp_tools:
                tool_map[t.name] = t
            logger.info("mcp_tools_added_to_agent", count=len(mcp_tools))

        if allowed_tools:
            active_tools = [t for t in tools if t.name in allowed_tools]
        else:
            active_tools = tools

        # Always keep chat fallback so the agent can respond
        if not any(t.name == "chat" for t in active_tools) and "chat" in tool_map:
            active_tools.append(tool_map["chat"])

        agent = create_react_agent(self.llm, active_tools)

        text = message.lower()
        if "pdf" in tool_map and any(word in text for word in ["pdf", "document", "file", "summarize", "summary"]):
            if allowed_tools is None or "pdf" in allowed_tools:
                result = await tool_map["pdf"].ainvoke({"question": message})
                return {
                    "response": result,
                    "category": RouterCategory.pdf.value,
                    "route_log": [RouterCategory.pdf.value],
                    "intent": RouterCategory.pdf.value,
                    "structured_data": None,
                }

        result = await agent.ainvoke({"messages": [HumanMessage(content=message)]})
        messages: List[Any] = result.get("messages", [])
        content = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                content = msg.content
                break
        return {
            "response": content or "No response",
            "category": last_tool["name"],
            "route_log": [last_tool["name"]],
            "intent": last_tool["name"],
            "structured_data": last_tool.get("structured_data"),
            "media_url": last_tool.get("media_url"),
        }


def build_tool_agent(
    settings,
    credentials: Dict[str, Any] | None = None,
    db=None,
    user_id: Optional[UUID] = None,
):
    """Factory for ToolAgent to keep existing imports simple."""
    return ToolAgent(settings, credentials=credentials, db=db, user_id=user_id)
