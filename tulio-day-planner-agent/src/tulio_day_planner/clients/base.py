"""Base utilities for calling Composio MCP tools."""
from __future__ import annotations

from typing import Any, Mapping, Protocol


class ToolRunner(Protocol):
    """Protocol representing the minimal MCP interface used by the clients."""

    def invoke(self, tool_name: str, *, arguments: Mapping[str, Any] | None = None) -> Any:
        ...


class BaseComposioClient:
    """Common functionality for Composio-powered clients."""

    def __init__(self, runner: ToolRunner) -> None:
        self._runner = runner

    def _invoke(self, tool_name: str, **arguments: Any) -> Any:
        return self._runner.invoke(tool_name, arguments=arguments or None)


__all__ = ["ToolRunner", "BaseComposioClient"]
