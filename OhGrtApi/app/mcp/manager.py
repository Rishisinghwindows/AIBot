"""
MCP Connection Manager

Provides:
- Tool caching (reduces latency)
- Connection pooling (reuses connections)
- Health checks (monitors server status)
- Automatic reconnection

Usage:
    manager = MCPManager.get_instance()
    tools = await manager.get_tools_for_user(db, user_id)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from enum import Enum

from app.logger import logger
from app.mcp.client import MCPClient
from app.mcp.types import MCPTool


class ServerStatus(str, Enum):
    """MCP server connection status."""
    UNKNOWN = "unknown"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


@dataclass
class CachedTools:
    """Cached tools from an MCP server."""
    tools: List[MCPTool]
    cached_at: datetime
    ttl_seconds: int = 300  # 5 minutes default

    @property
    def is_expired(self) -> bool:
        return (datetime.utcnow() - self.cached_at).total_seconds() > self.ttl_seconds


@dataclass
class ServerConnection:
    """Represents a connection to an MCP server."""
    name: str
    url: str
    token: Optional[str] = None
    status: ServerStatus = ServerStatus.UNKNOWN
    last_check: Optional[datetime] = None
    last_error: Optional[str] = None
    tool_count: int = 0
    latency_ms: Optional[float] = None


@dataclass
class MCPServerState:
    """Complete state for an MCP server."""
    connection: ServerConnection
    cached_tools: Optional[CachedTools] = None
    client: Optional[MCPClient] = None


class MCPManager:
    """
    Singleton manager for MCP server connections.

    Features:
    - Tool caching with configurable TTL
    - Connection pooling (lazy connections)
    - Background health checks
    - Per-user server isolation
    """

    _instance: Optional["MCPManager"] = None
    _lock: asyncio.Lock = asyncio.Lock()

    # Configuration
    DEFAULT_CACHE_TTL = 300  # 5 minutes
    HEALTH_CHECK_INTERVAL = 60  # 1 minute
    CONNECTION_TIMEOUT = 10  # seconds
    MAX_RETRIES = 3

    def __init__(self):
        # user_id -> server_name -> MCPServerState
        self._servers: Dict[str, Dict[str, MCPServerState]] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        self._cache_ttl = self.DEFAULT_CACHE_TTL

    @classmethod
    def get_instance(cls) -> "MCPManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    async def get_instance_async(cls) -> "MCPManager":
        """Get singleton instance (async-safe)."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def set_cache_ttl(self, seconds: int) -> None:
        """Set cache TTL for tool discovery."""
        self._cache_ttl = seconds

    # =========================================================================
    # Server Management
    # =========================================================================

    def _get_user_key(self, user_id: Optional[UUID]) -> str:
        """Get user key for server storage."""
        return str(user_id) if user_id else "anonymous"

    def _get_server_state(
        self,
        user_id: Optional[UUID],
        server_name: str
    ) -> Optional[MCPServerState]:
        """Get server state for a user."""
        user_key = self._get_user_key(user_id)
        return self._servers.get(user_key, {}).get(server_name)

    def _set_server_state(
        self,
        user_id: Optional[UUID],
        server_name: str,
        state: MCPServerState
    ) -> None:
        """Set server state for a user."""
        user_key = self._get_user_key(user_id)
        if user_key not in self._servers:
            self._servers[user_key] = {}
        self._servers[user_key][server_name] = state

    async def register_server(
        self,
        user_id: Optional[UUID],
        name: str,
        url: str,
        token: Optional[str] = None,
    ) -> ServerConnection:
        """
        Register an MCP server for a user.

        Args:
            user_id: User ID
            name: Server name
            url: Server URL
            token: Optional auth token

        Returns:
            ServerConnection with status
        """
        connection = ServerConnection(
            name=name,
            url=url,
            token=token,
            status=ServerStatus.UNKNOWN,
        )

        state = MCPServerState(connection=connection)
        self._set_server_state(user_id, name, state)

        # Test connection and discover tools
        await self._refresh_server(user_id, name)

        return self._get_server_state(user_id, name).connection

    async def unregister_server(
        self,
        user_id: Optional[UUID],
        name: str,
    ) -> bool:
        """Remove an MCP server for a user."""
        user_key = self._get_user_key(user_id)
        if user_key in self._servers and name in self._servers[user_key]:
            state = self._servers[user_key].pop(name)
            # Close client if exists
            if state.client:
                try:
                    await state.client.__aexit__(None, None, None)
                except Exception:
                    pass
            return True
        return False

    # =========================================================================
    # Tool Discovery & Caching
    # =========================================================================

    async def get_tools(
        self,
        user_id: Optional[UUID],
        server_name: str,
        force_refresh: bool = False,
    ) -> List[MCPTool]:
        """
        Get tools from a server (cached).

        Args:
            user_id: User ID
            server_name: Server name
            force_refresh: Force cache refresh

        Returns:
            List of MCPTool
        """
        state = self._get_server_state(user_id, server_name)
        if not state:
            return []

        # Check cache
        if not force_refresh and state.cached_tools and not state.cached_tools.is_expired:
            logger.debug(
                "mcp_cache_hit",
                server=server_name,
                tool_count=len(state.cached_tools.tools),
            )
            return state.cached_tools.tools

        # Refresh from server
        await self._refresh_server(user_id, server_name)

        state = self._get_server_state(user_id, server_name)
        return state.cached_tools.tools if state and state.cached_tools else []

    async def get_all_tools_for_user(
        self,
        db,
        user_id: Optional[UUID],
        force_refresh: bool = False,
    ) -> Dict[str, List[MCPTool]]:
        """
        Get all tools from all user's MCP servers.

        Args:
            db: Database session
            user_id: User ID
            force_refresh: Force cache refresh

        Returns:
            Dict mapping server name to tools
        """
        if not user_id:
            return {}

        # Load server configs from DB
        await self._load_servers_from_db(db, user_id)

        user_key = self._get_user_key(user_id)
        user_servers = self._servers.get(user_key, {})

        all_tools = {}

        # Fetch tools from all servers concurrently
        tasks = []
        server_names = []

        for server_name in user_servers:
            tasks.append(self.get_tools(user_id, server_name, force_refresh))
            server_names.append(server_name)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for server_name, result in zip(server_names, results):
                if isinstance(result, Exception):
                    logger.warning(
                        "mcp_get_tools_failed",
                        server=server_name,
                        error=str(result),
                    )
                    all_tools[server_name] = []
                else:
                    all_tools[server_name] = result

        return all_tools

    async def _load_servers_from_db(self, db, user_id: UUID) -> None:
        """Load MCP server configurations from database."""
        from app.db.models import IntegrationCredential
        from app.utils.crypto import decrypt_if_needed

        credentials = (
            db.query(IntegrationCredential)
            .filter(
                IntegrationCredential.user_id == user_id,
                IntegrationCredential.provider.like("mcp_server_%"),
            )
            .all()
        )

        for cred in credentials:
            config = cred.config or {}
            server_name = config.get("name", cred.provider.replace("mcp_server_", ""))
            url = config.get("url")

            if not url:
                continue

            # Check if already registered
            existing = self._get_server_state(user_id, server_name)
            if existing and existing.connection.url == url:
                continue  # Already registered

            # Decrypt token
            token = None
            if cred.access_token:
                try:
                    token = decrypt_if_needed(cred.access_token)
                except Exception:
                    token = cred.access_token

            # Register server
            connection = ServerConnection(
                name=server_name,
                url=url,
                token=token,
                status=ServerStatus.UNKNOWN,
            )
            state = MCPServerState(connection=connection)
            self._set_server_state(user_id, server_name, state)

    async def _refresh_server(
        self,
        user_id: Optional[UUID],
        server_name: str,
    ) -> None:
        """Refresh tools from an MCP server."""
        state = self._get_server_state(user_id, server_name)
        if not state:
            return

        connection = state.connection
        connection.status = ServerStatus.CONNECTING

        start_time = datetime.utcnow()

        try:
            client = MCPClient(
                base_url=connection.url,
                token=connection.token,
            )

            async with client:
                tools = await client.list_tools()

                # Update state
                elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
                connection.status = ServerStatus.CONNECTED
                connection.last_check = datetime.utcnow()
                connection.last_error = None
                connection.tool_count = len(tools)
                connection.latency_ms = elapsed

                state.cached_tools = CachedTools(
                    tools=tools,
                    cached_at=datetime.utcnow(),
                    ttl_seconds=self._cache_ttl,
                )

                logger.info(
                    "mcp_server_refreshed",
                    server=server_name,
                    tool_count=len(tools),
                    latency_ms=elapsed,
                )

        except Exception as e:
            connection.status = ServerStatus.ERROR
            connection.last_check = datetime.utcnow()
            connection.last_error = str(e)

            logger.warning(
                "mcp_server_refresh_failed",
                server=server_name,
                error=str(e),
            )

    # =========================================================================
    # Health Checks
    # =========================================================================

    async def start_health_checks(self) -> None:
        """Start background health check task."""
        if self._running:
            return

        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("mcp_health_checks_started")

    async def stop_health_checks(self) -> None:
        """Stop background health check task."""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("mcp_health_checks_stopped")

    async def _health_check_loop(self) -> None:
        """Background loop for health checks."""
        while self._running:
            try:
                await self._run_health_checks()
            except Exception as e:
                logger.error("mcp_health_check_error", error=str(e))

            await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)

    async def _run_health_checks(self) -> None:
        """Run health checks on all registered servers."""
        tasks = []
        server_ids = []  # (user_key, server_name)

        for user_key, servers in self._servers.items():
            for server_name, state in servers.items():
                # Skip if recently checked
                if state.connection.last_check:
                    elapsed = (datetime.utcnow() - state.connection.last_check).total_seconds()
                    if elapsed < self.HEALTH_CHECK_INTERVAL:
                        continue

                tasks.append(self._check_server_health(state))
                server_ids.append((user_key, server_name))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug("mcp_health_checks_completed", count=len(tasks))

    async def _check_server_health(self, state: MCPServerState) -> None:
        """Check health of a single server."""
        connection = state.connection
        start_time = datetime.utcnow()

        try:
            client = MCPClient(
                base_url=connection.url,
                token=connection.token,
            )

            async with client:
                # Just list tools to verify connection
                tools = await client.list_tools()

                elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
                connection.status = ServerStatus.CONNECTED
                connection.last_check = datetime.utcnow()
                connection.last_error = None
                connection.tool_count = len(tools)
                connection.latency_ms = elapsed

                # Update cache if expired
                if not state.cached_tools or state.cached_tools.is_expired:
                    state.cached_tools = CachedTools(
                        tools=tools,
                        cached_at=datetime.utcnow(),
                        ttl_seconds=self._cache_ttl,
                    )

        except Exception as e:
            connection.status = ServerStatus.ERROR
            connection.last_check = datetime.utcnow()
            connection.last_error = str(e)

    # =========================================================================
    # Status & Metrics
    # =========================================================================

    def get_server_status(
        self,
        user_id: Optional[UUID],
        server_name: str,
    ) -> Optional[ServerConnection]:
        """Get status of a specific server."""
        state = self._get_server_state(user_id, server_name)
        return state.connection if state else None

    def get_all_server_status(
        self,
        user_id: Optional[UUID],
    ) -> List[ServerConnection]:
        """Get status of all servers for a user."""
        user_key = self._get_user_key(user_id)
        user_servers = self._servers.get(user_key, {})
        return [state.connection for state in user_servers.values()]

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        total_servers = sum(len(servers) for servers in self._servers.values())
        total_users = len(self._servers)

        connected = 0
        errored = 0
        total_tools = 0

        for servers in self._servers.values():
            for state in servers.values():
                if state.connection.status == ServerStatus.CONNECTED:
                    connected += 1
                elif state.connection.status == ServerStatus.ERROR:
                    errored += 1
                total_tools += state.connection.tool_count

        return {
            "total_users": total_users,
            "total_servers": total_servers,
            "connected_servers": connected,
            "errored_servers": errored,
            "total_tools": total_tools,
            "cache_ttl_seconds": self._cache_ttl,
            "health_check_running": self._running,
        }

    def invalidate_cache(
        self,
        user_id: Optional[UUID] = None,
        server_name: Optional[str] = None,
    ) -> int:
        """
        Invalidate tool cache.

        Args:
            user_id: Specific user (None = all users)
            server_name: Specific server (None = all servers)

        Returns:
            Number of caches invalidated
        """
        count = 0

        if user_id is not None:
            user_key = self._get_user_key(user_id)
            if user_key in self._servers:
                if server_name:
                    if server_name in self._servers[user_key]:
                        self._servers[user_key][server_name].cached_tools = None
                        count = 1
                else:
                    for state in self._servers[user_key].values():
                        state.cached_tools = None
                        count += 1
        else:
            for servers in self._servers.values():
                if server_name:
                    if server_name in servers:
                        servers[server_name].cached_tools = None
                        count += 1
                else:
                    for state in servers.values():
                        state.cached_tools = None
                        count += 1

        logger.info("mcp_cache_invalidated", count=count)
        return count


# Convenience function
async def get_mcp_manager() -> MCPManager:
    """Get the singleton MCP manager instance."""
    return await MCPManager.get_instance_async()
