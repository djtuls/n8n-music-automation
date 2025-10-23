"""Utilities for writing to Notion."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable, List, Mapping


@dataclass
class NotionPage:
    page_id: str
    properties: Mapping[str, object]


class NotionClient:
    """Abstraction over the Notion API.

    The concrete API wiring should use the official Notion SDK and supply a
    callable that produces an authenticated client.
    """

    def __init__(self, client_factory):
        self._client_factory = client_factory

    def upsert_page(self, database_id: str, properties: Mapping[str, object]) -> NotionPage:
        """Create or update a page in the given database."""

        raise NotImplementedError("Inject a Notion API client implementation")

    def query_database(self, database_id: str, filter_: Mapping[str, object]) -> List[NotionPage]:
        """Return pages in ``database_id`` that match ``filter_``."""

        raise NotImplementedError("Inject a Notion API client implementation")

    def append_block_children(self, page_id: str, blocks: Iterable[Mapping[str, object]]) -> None:
        """Append block children to a Notion page."""

        raise NotImplementedError("Inject a Notion API client implementation")

    def log_sync(self, database_id: str, service: str, operation: str, error: str | None = None) -> None:
        """Convenience helper for recording sync log entries."""

        timestamp = dt.datetime.utcnow().isoformat()
        properties = {
            "Timestamp": {"date": {"start": timestamp}},
            "Service": {"select": {"name": service}},
            "Operation": {"title": [{"type": "text", "text": {"content": operation}}]},
        }
        if error:
            properties["Error"] = {"rich_text": [{"type": "text", "text": {"content": error}}]}
        self.upsert_page(database_id, properties)
