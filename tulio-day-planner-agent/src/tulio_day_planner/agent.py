"""High level helpers to build and run the Tulio day planner agent."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Mapping, MutableMapping, Optional, Sequence

from .config import NotionConfig
from .notion_client import NotionClient
from .sync import MirrorWriter, PlannerSyncPipeline, PlannerWriter


def _coerce_sequence(value: Optional[Iterable[Mapping[str, object]]]) -> Optional[Sequence[Mapping[str, object]]]:
    if value is None:
        return None
    if isinstance(value, Sequence):
        return value  # type: ignore[return-value]
    return list(value)


def default_planner_writer(notion_client: NotionClient) -> PlannerWriter:
    """Return a planner writer that creates or updates Notion pages."""

    def _writer(database_id: str, entries: Sequence[Mapping[str, object]]) -> None:
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise TypeError("Planner entries must be mappings")

            properties = entry.get("properties")
            if not isinstance(properties, Mapping):
                raise ValueError("Planner entries must include a 'properties' mapping")

            page_id = entry.get("id") or entry.get("page_id")
            children = _coerce_sequence(entry.get("children"))
            icon = entry.get("icon") if isinstance(entry.get("icon"), Mapping) else None
            cover = entry.get("cover") if isinstance(entry.get("cover"), Mapping) else None

            if page_id:
                notion_client.update_page(
                    str(page_id),
                    properties=properties,
                    icon=icon,
                    cover=cover,
                )
            else:
                notion_client.create_page(
                    database_id,
                    properties=properties,
                    children=children,
                    icon=icon,
                    cover=cover,
                )

    return _writer


def default_mirror_writer(notion_client: NotionClient) -> MirrorWriter:
    """Return a mirror writer that appends rows into the mirror database."""

    def _writer(database_id: str, entries: Iterable[Mapping[str, object]]) -> None:
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise TypeError("Mirror entries must be mappings")

            properties = entry.get("properties")
            if not isinstance(properties, Mapping):
                raise ValueError("Mirror entries must include a 'properties' mapping")

            children = _coerce_sequence(entry.get("children"))
            icon = entry.get("icon") if isinstance(entry.get("icon"), Mapping) else None
            cover = entry.get("cover") if isinstance(entry.get("cover"), Mapping) else None

            notion_client.create_page(
                database_id,
                properties=properties,
                children=children,
                icon=icon,
                cover=cover,
            )

    return _writer


@dataclass
class TulioDayPlannerAgent:
    """Concrete agent that provisions Notion and syncs planner data."""

    config: NotionConfig
    notion_client: NotionClient
    pipeline: PlannerSyncPipeline

    @classmethod
    def from_environment(
        cls,
        *,
        orchestrator: Optional[object] = None,
        env: Optional[Mapping[str, str]] = None,
        planner_writer: Optional[PlannerWriter] = None,
        mirror_writer: Optional[MirrorWriter] = None,
        composio_client: Optional[object] = None,
        session: Optional[object] = None,
    ) -> "TulioDayPlannerAgent":
        """Instantiate the agent using environment variables and optional orchestrator."""

        env_mapping: Mapping[str, str]
        if env is None:
            env_mapping = os.environ
        else:
            env_mapping = env

        config = NotionConfig.from_env(env_mapping, orchestrator=orchestrator)
        notion_client = NotionClient(
            config,
            composio_client=composio_client,
            orchestrator=orchestrator,
            session=session,
        )

        planner_writer = planner_writer or default_planner_writer(notion_client)
        mirror_writer = mirror_writer or default_mirror_writer(notion_client)

        pipeline = PlannerSyncPipeline(
            notion_client=notion_client,
            planner_writer=planner_writer,
            mirror_writer=mirror_writer,
        )

        return cls(config=config, notion_client=notion_client, pipeline=pipeline)

    def sync(
        self,
        planner_entries: Sequence[Mapping[str, object]],
        mirror_entries: Iterable[Mapping[str, object]],
    ) -> MutableMapping[str, str]:
        """Run a sync and return the resolved database identifiers."""

        self.pipeline.run(planner_entries, mirror_entries)
        return self.notion_client.cached_database_ids

    def ensure_databases(self) -> MutableMapping[str, str]:
        """Resolve (and provision) the Notion databases for the agent."""

        return self.notion_client.ensure_databases()
