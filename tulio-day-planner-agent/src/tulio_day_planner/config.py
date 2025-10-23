"""Configuration helpers for the Tulio day planner agent.

This module centralises all configuration related to the data sources used by
``sync_day_planner``.  The agent primarily relies on Composio MCP tools, so the
configuration exposes identifiers that those tools expect.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence
import os


def _split_csv(value: str | None) -> list[str]:
    """Split a comma separated string into a cleaned list of tokens."""
    if not value:
        return []
    return [token.strip() for token in value.split(",") if token.strip()]


def _normalise(value: Sequence[str] | str | None) -> list[str]:
    """Normalise override values into list form."""
    if value is None:
        return []
    if isinstance(value, str):
        return _split_csv(value)
    return list(value)



@dataclass(slots=True)
class PlannerConfig:
    """Strongly typed configuration for the planner synchronisation."""

    drive_folder_ids: list[str] = field(default_factory=list)
    todoist_project_filters: list[str] = field(default_factory=list)
    whatsapp_channel_ids: list[str] = field(default_factory=list)
    gmail_label_filter: str | None = None
    calendar_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "PlannerConfig":
        """Build a configuration instance from environment variables."""
        env = env or os.environ
        return cls(
            drive_folder_ids=_split_csv(env.get("DAY_PLANNER_DRIVE_FOLDER_IDS")),
            todoist_project_filters=_split_csv(
                env.get("DAY_PLANNER_TODOIST_PROJECT_FILTERS")
            ),
            whatsapp_channel_ids=_split_csv(
                env.get("DAY_PLANNER_WHATSAPP_CHANNEL_IDS")
            ),
            gmail_label_filter=env.get("DAY_PLANNER_GMAIL_LABEL_FILTER"),
            calendar_ids=_split_csv(env.get("DAY_PLANNER_CALENDAR_IDS")),
        )

    def merge_overrides(self, **overrides: Sequence[str] | str | None) -> "PlannerConfig":
        """Return a copy of the configuration with supplied overrides applied."""
        return PlannerConfig(
            drive_folder_ids=_normalise(overrides.get("drive_folder_ids", self.drive_folder_ids)),
            todoist_project_filters=_normalise(overrides.get("todoist_project_filters", self.todoist_project_filters)),
            whatsapp_channel_ids=_normalise(overrides.get("whatsapp_channel_ids", self.whatsapp_channel_ids)),
            gmail_label_filter=overrides.get("gmail_label_filter", self.gmail_label_filter),
            calendar_ids=_normalise(overrides.get("calendar_ids", self.calendar_ids)),
        )

    def as_tool_arguments(self) -> dict[str, list[str] | str | None]:
        """Represent the configuration as arguments suitable for MCP calls."""
        return {
            "drive_folder_ids": self.drive_folder_ids,
            "todoist_project_filters": self.todoist_project_filters,
            "whatsapp_channel_ids": self.whatsapp_channel_ids,
            "gmail_label_filter": self.gmail_label_filter,
            "calendar_ids": self.calendar_ids,
        }


__all__ = ["PlannerConfig"]
