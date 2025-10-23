"""Core orchestration for synchronising the day planner."""
from __future__ import annotations

from typing import Any, Iterable

from .clients import DriveClient, TodoistClient, WhatsAppClient
from .clients.base import ToolRunner
from .config import PlannerConfig

GMAIL_TOOL = "google_gmail:list_messages"
CALENDAR_TOOL = "google_calendar:list_events"


def _fetch_gmail_messages(runner: ToolRunner, label_filter: str | None) -> list[dict[str, Any]]:
    arguments: dict[str, Any] = {"max_results": 50}
    if label_filter:
        arguments["label_filter"] = label_filter
    response = runner.invoke(GMAIL_TOOL, arguments=arguments)
    if isinstance(response, dict) and "messages" in response:
        return response["messages"]
    return response if isinstance(response, list) else []


def _fetch_calendar_events(runner: ToolRunner, calendar_ids: Iterable[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    ids = list(calendar_ids) or [None]
    for calendar_id in ids:
        arguments: dict[str, Any] = {"max_results": 50}
        if calendar_id:
            arguments["calendar_id"] = calendar_id
        response = runner.invoke(CALENDAR_TOOL, arguments=arguments)
        if isinstance(response, dict) and "events" in response:
            items = response["events"]
        elif isinstance(response, list):
            items = response
        else:
            items = []
        events.extend(
            {
                "calendar_id": calendar_id,
                "event": item,
            }
            for item in items
        )
    return events


def _build_payload(
    *,
    drive_folders: list[dict[str, Any]],
    todoist_projects: list[dict[str, Any]],
    whatsapp_chats: list[dict[str, Any]],
    gmail_messages: list[dict[str, Any]],
    calendar_events: list[dict[str, Any]],
    config: PlannerConfig,
) -> dict[str, Any]:
    return {
        "sources": {
            "drive": {"folders": drive_folders},
            "todoist": {"projects": todoist_projects},
            "whatsapp": {"chats": whatsapp_chats},
            "gmail": {
                "label_filter": config.gmail_label_filter,
                "messages": gmail_messages,
            },
            "calendar": {
                "calendar_ids": config.calendar_ids,
                "events": calendar_events,
            },
        },
        "summary": {
            "drive_files": sum(len(folder.get("files", [])) for folder in drive_folders),
            "todoist_tasks": sum(len(project.get("tasks", [])) for project in todoist_projects),
            "whatsapp_messages": sum(len(chat.get("messages", [])) for chat in whatsapp_chats),
            "gmail_messages": len(gmail_messages),
            "calendar_events": len(calendar_events),
        },
    }


def sync_day_planner(runner: ToolRunner, config: PlannerConfig | None = None) -> dict[str, Any]:
    """Synchronise all planner data sources via their respective MCP tools."""

    config = config or PlannerConfig.from_env()

    drive_client = DriveClient(runner)
    todoist_client = TodoistClient(runner)
    whatsapp_client = WhatsAppClient(runner)

    drive_folders = drive_client.fetch_folders(config.drive_folder_ids)
    todoist_projects = todoist_client.fetch_tasks(config.todoist_project_filters)
    whatsapp_chats = whatsapp_client.fetch_chats(config.whatsapp_channel_ids)
    gmail_messages = _fetch_gmail_messages(runner, config.gmail_label_filter)
    calendar_events = _fetch_calendar_events(runner, config.calendar_ids)

    return _build_payload(
        drive_folders=drive_folders,
        todoist_projects=todoist_projects,
        whatsapp_chats=whatsapp_chats,
        gmail_messages=gmail_messages,
        calendar_events=calendar_events,
        config=config,
    )


__all__ = ["sync_day_planner"]
