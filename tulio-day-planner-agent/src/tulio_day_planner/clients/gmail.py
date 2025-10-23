"""Gmail client utilities."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class GmailMessage:
    thread_id: str
    message_id: str
    subject: str
    sender: str
    snippet: str
    internal_date: dt.datetime
    labels: List[str]


class GmailClient:
    """Thin wrapper around the Gmail API.

    This module deliberately avoids importing the Google SDK so that the agent
    can be deployed in runtimes where the package is not preinstalled.  The
    `fetch_messages` method is expected to be implemented by wiring this class
    to an authenticated Gmail API service (e.g., via `googleapiclient` or
    `gmail-api-python-client`).
    """

    def __init__(self, service_factory):
        self._service_factory = service_factory

    def fetch_messages(
        self,
        query: str,
        labels: Optional[Iterable[str]] = None,
        max_results: int = 50,
    ) -> List[GmailMessage]:
        """Fetch messages matching a Gmail search query.

        Args:
            query: Gmail query syntax string.
            labels: Optional iterable of label IDs to restrict the search.
            max_results: Maximum number of threads to return.

        Returns:
            List of :class:`GmailMessage` instances.  The base implementation
            raises ``NotImplementedError`` so that host environments can inject
            their own API logic.
        """

        raise NotImplementedError("Inject a Gmail API client implementation")

    def get_history_id(self) -> Optional[str]:
        """Return the latest history ID for incremental syncs."""

        raise NotImplementedError("Inject a Gmail API client implementation")
