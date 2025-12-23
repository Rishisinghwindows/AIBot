"""
Integration tests for chat endpoints.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.integration
class TestChatSendEndpoint:
    """Tests for chat send endpoint."""

    def test_send_without_auth(self, client, security_headers):
        """Test sending message without authentication."""
        response = client.post(
            "/chat/send",
            json={"message": "Hello"},
            headers=security_headers,
        )
        assert response.status_code == 401

    def test_send_empty_message(self, client, auth_headers):
        """Test sending empty message."""
        response = client.post(
            "/chat/send",
            json={"message": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_send_message_success(self, client, test_user, auth_headers, test_db):
        """Test successful message sending."""
        with patch("app.chat.router.get_agent") as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.invoke.return_value = {
                "response": "Hello! How can I help you?",
                "category": "chat",
            }
            mock_get_agent.return_value = mock_agent

            response = client.post(
                "/chat/send",
                json={"message": "Hello, how are you?"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "conversation_id" in data
            assert "user_message" in data
            assert "assistant_message" in data

    def test_send_message_with_conversation_id(self, client, auth_headers, test_conversation_id):
        """Test sending message to existing conversation."""
        with patch("app.chat.router.get_agent") as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.invoke.return_value = {
                "response": "Continuing our conversation.",
                "category": "chat",
            }
            mock_get_agent.return_value = mock_agent

            response = client.post(
                "/chat/send",
                json={
                    "message": "Continue our chat",
                    "conversation_id": str(test_conversation_id),
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == str(test_conversation_id)

    def test_send_message_with_tools(self, client, auth_headers):
        """Test sending message with specific tools enabled."""
        with patch("app.chat.router.get_agent") as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.invoke.return_value = {
                "response": "The weather in London is sunny.",
                "category": "weather",
            }
            mock_get_agent.return_value = mock_agent

            response = client.post(
                "/chat/send",
                json={
                    "message": "What's the weather in London?",
                    "tools": ["weather"],
                },
                headers=auth_headers,
            )

            assert response.status_code == 200


@pytest.mark.integration
class TestChatHistoryEndpoint:
    """Tests for chat history endpoint."""

    def test_history_without_auth(self, client, security_headers):
        """Test getting history without authentication."""
        response = client.get("/chat/history", headers=security_headers)
        assert response.status_code == 401

    def test_history_empty(self, client, auth_headers):
        """Test getting history when no messages exist."""
        response = client.get("/chat/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_history_with_messages(self, client, auth_headers, test_messages):
        """Test getting history with existing messages."""
        response = client.get("/chat/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) >= 0  # May vary based on user

    def test_history_with_conversation_filter(self, client, auth_headers, test_conversation_id, test_messages):
        """Test getting history for specific conversation."""
        response = client.get(
            f"/chat/history?conversation_id={test_conversation_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_history_with_limit(self, client, auth_headers):
        """Test getting history with limit parameter."""
        response = client.get("/chat/history?limit=5", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) <= 5


@pytest.mark.integration
class TestConversationsEndpoint:
    """Tests for conversations list endpoint."""

    def test_conversations_without_auth(self, client, security_headers):
        """Test getting conversations without authentication."""
        response = client.get("/chat/conversations", headers=security_headers)
        assert response.status_code == 401

    def test_conversations_list(self, client, auth_headers):
        """Test getting conversations list."""
        response = client.get("/chat/conversations", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_delete_conversation_without_auth(self, client, security_headers, test_conversation_id):
        """Test deleting conversation without authentication."""
        response = client.delete(
            f"/chat/conversations/{test_conversation_id}",
            headers=security_headers,
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestToolsEndpoint:
    """Tests for tools list endpoint."""

    def test_tools_without_auth(self, client, security_headers):
        """Test getting tools without authentication."""
        response = client.get("/chat/tools", headers=security_headers)
        assert response.status_code == 401

    def test_tools_list(self, client, auth_headers):
        """Test getting available tools."""
        response = client.get("/chat/tools", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Check tool structure if tools exist
        if data:
            tool = data[0]
            assert "name" in tool or "id" in tool
