"""Main orchestration entrypoint for the Tulio Day Planner agent."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Dict, Iterable, List

from .clients.calendar import CalendarClient, CalendarEvent
from .clients.gmail import GmailClient, GmailMessage
from .clients.notion import NotionClient
from .config import load_config

LOGGER = logging.getLogger(__name__)


def classify_message(message: GmailMessage) -> str:
    """Naive classification based on subject heuristics.

    The Agent Builder runtime can replace this logic with an LLM classifier.
    """

    subject = message.subject.lower()
    if any(keyword in subject for keyword in {"follow up", "follow-up"}):
        return "Follow-up"
    if any(keyword in subject for keyword in {"meeting", "call", "sync"}):
        return "Meeting"
    if any(keyword in subject for keyword in {"task", "action", "due"}):
        return "Task"
    return "Info"


def summarize_messages(messages: Iterable[GmailMessage]) -> List[str]:
    """Return bullet summaries for Gmail messages.

    Replace with GPT-powered summarization in production.
    """

    bullets = []
    for message in messages:
        bullets.append(f"• {message.subject} — from {message.sender}")
    return bullets


def summarize_events(events: Iterable[CalendarEvent]) -> List[str]:
    bullets = []
    for event in events:
        start = event.start.strftime("%H:%M")
        end = event.end.strftime("%H:%M")
        bullets.append(f"• {start}–{end} {event.summary}")
    return bullets


def sync_day_planner(
    gmail_client: GmailClient,
    calendar_client: CalendarClient,
    notion_client: NotionClient,
) -> Dict[str, List[str]]:
    """Execute the full planner synchronization and return summary bullets."""

    _gmail_config, _calendar_config, notion_config, settings, schema = load_config()

    LOGGER.info("Starting Tulio Day Planner sync")
    now = dt.datetime.utcnow()
    start = now - dt.timedelta(hours=24)
    end = now + dt.timedelta(days=settings.sync_range_days)

    messages = gmail_client.fetch_messages(
        query=f"after:{int(start.timestamp())}",
        max_results=100,
    )
    events = calendar_client.list_events(settings.calendar_id, now, end)

    LOGGER.debug("Fetched %s Gmail messages", len(messages))
    LOGGER.debug("Fetched %s calendar events", len(events))

    message_summaries = summarize_messages(messages)
    event_summaries = summarize_events(events)

    notion_client.log_sync(notion_config.log_db, "Gmail", "Fetched messages")
    notion_client.log_sync(notion_config.log_db, "Calendar", "Fetched events")

    day_planner_blocks: List[dict] = [
        {"type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "Emails"}}]}}
    ]
    for item in message_summaries:
        day_planner_blocks.append(
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": item}}]},
            }
        )

    day_planner_blocks.append(
        {"type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "Meetings"}}]}}
    )
    for item in event_summaries:
        day_planner_blocks.append(
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": item}}]},
            }
        )

    today = dt.date.today().isoformat()
    day_planner_page = notion_client.upsert_page(
        notion_config.day_planner_db,
        {
            schema.day_planner["title"]: {
                "title": [
                    {
                        "text": {
                            "content": f"📅 {today} — Day Planner",
                        }
                    }
                ]
            },
            schema.day_planner["date"]: {"date": {"start": today}},
            schema.day_planner["new_emails"]: {"number": len(messages)},
            schema.day_planner["meetings"]: {"number": len(events)},
            schema.day_planner["tasks_due"]: {"number": 0},
            schema.day_planner["follow_ups"]: {"number": 0},
            schema.day_planner["last_synced"]: {"date": {"start": now.isoformat()}},
        },
    )

    notion_client.append_block_children(day_planner_page.page_id, day_planner_blocks)

    LOGGER.info("Tulio Day Planner sync complete")

    return {
        "emails": message_summaries,
        "meetings": event_summaries,
    }


def main() -> None:
    """Entrypoint used by ``python -m tulio_day_planner.agent``."""

    raise SystemExit(
        "This module defines business logic only. Inject concrete API clients "
        "(Gmail, Calendar, Notion) via your orchestration platform and call "
        "`sync_day_planner` from there."
    )
