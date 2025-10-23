"""Sync pipeline for the Tulio day planner agent."""
from __future__ import annotations

from typing import Callable, Iterable, Mapping, Sequence

from .notion_client import NotionClient

PlannerWriter = Callable[[str, Sequence[Mapping[str, object]]], None]
MirrorWriter = Callable[[str, Iterable[Mapping[str, object]]], None]


class PlannerSyncPipeline:
    """Synchronise planner tasks and mirror entries into Notion."""

    def __init__(
        self,
        notion_client: NotionClient,
        *,
        planner_writer: PlannerWriter,
        mirror_writer: MirrorWriter,
    ) -> None:
        self.notion_client = notion_client
        self._planner_writer = planner_writer
        self._mirror_writer = mirror_writer

    def run(
        self,
        planner_entries: Sequence[Mapping[str, object]],
        mirror_entries: Iterable[Mapping[str, object]],
    ) -> None:
        """Execute the sync after making sure required databases exist."""

        database_ids = self.notion_client.ensure_databases()
        planner_database_id = database_ids["planner"]
        mirror_database_id = database_ids["mirror"]

        self._planner_writer(planner_database_id, planner_entries)
        self._mirror_writer(mirror_database_id, mirror_entries)

