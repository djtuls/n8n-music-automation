"""Google Drive client wrapper around the Composio MCP tools."""
from __future__ import annotations

from typing import Any, Iterable

from .base import BaseComposioClient, ToolRunner


class DriveClient(BaseComposioClient):
    """Client used to fetch Drive folder contents for the planner."""

    def __init__(self, runner: ToolRunner, *, list_files_tool: str = "google_drive:list_files") -> None:
        super().__init__(runner)
        self._list_files_tool = list_files_tool

    def fetch_folders(self, folder_ids: Iterable[str]) -> list[dict[str, Any]]:
        """Return a structured representation of each requested folder."""
        payload: list[dict[str, Any]] = []
        for folder_id in folder_ids:
            response = self._invoke(
                self._list_files_tool,
                folder_id=folder_id,
                include_folders=False,
                include_files=True,
            )
            if isinstance(response, dict) and "files" in response:
                files = response["files"]
            elif isinstance(response, list):
                files = response
            else:
                files = []
            payload.append(
                {
                    "folder_id": folder_id,
                    "files": files,
                }
            )
        return payload


__all__ = ["DriveClient"]
