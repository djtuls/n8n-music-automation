"""Configuration helpers and Notion schema definitions."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class OAuthConfig:
    client_id: str
    client_secret: str
    refresh_token: str
    scopes: List[str]


@dataclass(frozen=True)
class NotionConfig:
    token: str
    day_planner_db: str
    mirror_db: str
    log_db: str


@dataclass(frozen=True)
class AgentSettings:
    calendar_id: str
    sync_range_days: int
    summary_channel: str


@dataclass(frozen=True)
class PlannerSchema:
    """Canonical property names used in Notion databases."""

    day_planner: Dict[str, str]
    mirror: Dict[str, str]
    log: Dict[str, str]


DEFAULT_SCHEMA = PlannerSchema(
    day_planner={
        "title": "Name",
        "date": "Date",
        "new_emails": "New Emails",
        "meetings": "Meetings",
        "tasks_due": "Tasks Due",
        "follow_ups": "Follow-ups",
        "notes": "Notes",
        "last_synced": "Last Synced",
    },
    mirror={
        "title": "Name",
        "type": "Type",
        "status": "Status",
        "priority": "Priority",
        "due": "Due",
        "source_account": "Source Account",
        "sender": "Sender",
        "thread_id": "Gmail Thread ID",
        "message_id": "Gmail Message ID",
        "gmail_link": "Gmail Link",
        "tags": "Tags",
        "summary": "Summary",
        "last_synced": "Last Synced",
        "dedup_key": "Dedup Key",
    },
    log={
        "timestamp": "Timestamp",
        "service": "Service",
        "operation": "Operation",
        "error": "Error",
        "retry_result": "Retry Result",
    },
)


def load_config(schema: PlannerSchema = DEFAULT_SCHEMA) -> tuple[OAuthConfig, OAuthConfig, NotionConfig, AgentSettings, PlannerSchema]:
    """Load configuration from environment variables."""

    gmail = OAuthConfig(
        client_id=os.environ.get("GMAIL_CLIENT_ID", ""),
        client_secret=os.environ.get("GMAIL_CLIENT_SECRET", ""),
        refresh_token=os.environ.get("GMAIL_REFRESH_TOKEN", ""),
        scopes=[scope for scope in os.environ.get("GMAIL_SCOPES", "").split(",") if scope],
    )

    calendar = OAuthConfig(
        client_id=gmail.client_id,
        client_secret=gmail.client_secret,
        refresh_token=gmail.refresh_token,
        scopes=[scope for scope in os.environ.get("CALENDAR_SCOPES", "").split(",") if scope],
    )

    notion = NotionConfig(
        token=os.environ.get("NOTION_TOKEN", ""),
        day_planner_db=os.environ.get("NOTION_DB_PLANNER", ""),
        mirror_db=os.environ.get("NOTION_DB_MIRROR", ""),
        log_db=os.environ.get("NOTION_DB_LOG", ""),
    )

    settings = AgentSettings(
        calendar_id=os.environ.get("CALENDAR_ID", "primary"),
        sync_range_days=int(os.environ.get("SYNC_RANGE_DAYS", "2")),
        summary_channel=os.environ.get("SUMMARY_CHANNEL", "notion"),
    )

    return gmail, calendar, notion, settings, schema
