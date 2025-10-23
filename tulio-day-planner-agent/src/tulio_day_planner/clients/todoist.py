"""Todoist client wrapper around Composio MCP tools."""
from __future__ import annotations

from typing import Any, Iterable

from .base import BaseComposioClient, ToolRunner


class TodoistClient(BaseComposioClient):
    """Client responsible for retrieving Todoist tasks for the planner."""

    def __init__(self, runner: ToolRunner, *, list_tasks_tool: str = "todoist:list_tasks") -> None:
        super().__init__(runner)
        self._list_tasks_tool = list_tasks_tool

    def fetch_tasks(self, project_filters: Iterable[str]) -> list[dict[str, Any]]:
        """Fetch tasks for the provided filter expressions."""
        tasks: list[dict[str, Any]] = []
        for project_filter in project_filters:
            response = self._invoke(self._list_tasks_tool, filter=project_filter)
            if isinstance(response, dict) and "tasks" in response:
                task_items = response["tasks"]
            elif isinstance(response, list):
                task_items = response
            else:
                task_items = []
            tasks.append(
                {
                    "filter": project_filter,
                    "tasks": task_items,
                }
            )
        return tasks


__all__ = ["TodoistClient"]
