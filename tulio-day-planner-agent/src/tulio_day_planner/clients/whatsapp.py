"""WhatsApp client wrapper around Composio MCP tools."""
from __future__ import annotations

from typing import Any, Iterable

from .base import BaseComposioClient, ToolRunner


class WhatsAppClient(BaseComposioClient):
    """Client responsible for retrieving WhatsApp messages for the planner."""

    def __init__(
        self,
        runner: ToolRunner,
        *,
        list_channels_tool: str = "whatsapp:list_channels",
        list_messages_tool: str = "whatsapp:list_messages",
    ) -> None:
        super().__init__(runner)
        self._list_channels_tool = list_channels_tool
        self._list_messages_tool = list_messages_tool

    def fetch_channels(self) -> list[dict[str, Any]]:
        """Return a lightweight list of available WhatsApp channels."""
        response = self._invoke(self._list_channels_tool)
        if isinstance(response, dict) and "channels" in response:
            return response["channels"]
        if isinstance(response, list):
            return response
        return []

    def fetch_chats(self, channel_ids: Iterable[str]) -> list[dict[str, Any]]:
        """Fetch recent messages for the specified channels."""
        chats: list[dict[str, Any]] = []
        for channel_id in channel_ids:
            response = self._invoke(self._list_messages_tool, channel_id=channel_id)
            if isinstance(response, dict) and "messages" in response:
                messages = response["messages"]
            elif isinstance(response, list):
                messages = response
            else:
                messages = []
            chats.append(
                {
                    "channel_id": channel_id,
                    "messages": messages,
                }
            )
        return chats


__all__ = ["WhatsAppClient"]
