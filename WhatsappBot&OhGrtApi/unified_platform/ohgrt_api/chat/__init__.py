"""
Chat API module.
"""

from ohgrt_api.chat.router import router
from ohgrt_api.chat.service import ChatService
from ohgrt_api.chat.web_chat_api import (
    WebChatAPI,
    get_web_chat_api,
    process_web_message,
)

__all__ = [
    "router",
    "ChatService",
    "WebChatAPI",
    "get_web_chat_api",
    "process_web_message",
]
