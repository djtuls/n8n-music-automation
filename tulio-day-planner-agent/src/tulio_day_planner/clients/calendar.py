"""Google Calendar client utilities."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import List


@dataclass
class CalendarEvent:
    event_id: str
    summary: str
    start: dt.datetime
    end: dt.datetime
    attendees: List[str]
    hangout_link: str | None = None


class CalendarClient:
    """Minimal interface for retrieving calendar events."""

    def __init__(self, service_factory):
        self._service_factory = service_factory

    def list_events(self, calendar_id: str, start: dt.datetime, end: dt.datetime) -> List[CalendarEvent]:
        """Return all events between ``start`` and ``end`` (inclusive)."""

        raise NotImplementedError("Inject a Calendar API client implementation")
