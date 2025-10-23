"""Client helpers for provisioning Notion databases used by the planner."""
from __future__ import annotations

from typing import Dict, Iterable, Mapping, Optional

import requests

from .config import NotionConfig, NotionProvisioningInstructions


class NotionClient:
    """Wrapper around the Notion API with optional Composio integration.

    When supplied with a Composio orchestrator the client can automatically
    locate the appropriate assistant that exposes Notion database discovery and
    creation helpers.
    """

    notion_version = "2022-06-28"

    def __init__(
        self,
        config: NotionConfig,
        *,
        composio_client: Optional[object] = None,
        orchestrator: Optional[object] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.config = config
        self._provided_composio_client = composio_client
        self.orchestrator = orchestrator
        self.session = session or requests.Session()
        self._database_cache: Dict[str, str] = {}
        self._resolved_composio_client: Optional[object] = None
        self._resolved_composio_client_initialized = False

    @property
    def cached_database_ids(self) -> Dict[str, str]:
        """Return cached database identifiers."""

        return dict(self._database_cache)

    def ensure_databases(self) -> Dict[str, str]:
        """Ensure that both planner and mirror databases exist and return their IDs."""

        if self._database_cache:
            return dict(self._database_cache)

        planner_id = self.config.planner_database_id
        mirror_id = self.config.mirror_database_id

        if planner_id and mirror_id:
            self._database_cache = {"planner": planner_id, "mirror": mirror_id}
            return dict(self._database_cache)

        if not self.config.create_databases_when_missing:
            raise RuntimeError(
                "Database identifiers missing and auto provisioning disabled."
            )

        instructions = self.config.provisioning
        if instructions is None:
            raise RuntimeError(
                "Provisioning instructions are required when database identifiers are not provided."
            )

        discovered = self._discover_existing_databases(instructions)

        if not planner_id:
            planner_id = discovered.get("planner")
        if not mirror_id:
            mirror_id = discovered.get("mirror")

        ids_needed = {
            key: value
            for key, value in {"planner": planner_id, "mirror": mirror_id}.items()
            if not value
        }

        if ids_needed:
            created = self._create_missing_databases(instructions, ids_needed.keys())
            for key, value in created.items():
                ids_needed[key] = value

        planner_id = planner_id or ids_needed.get("planner")
        mirror_id = mirror_id or ids_needed.get("mirror")

        if not planner_id or not mirror_id:
            raise RuntimeError("Unable to provision both planner and mirror databases")

        self._database_cache = {"planner": planner_id, "mirror": mirror_id}
        return dict(self._database_cache)

    # Discovery helpers -------------------------------------------------

    def _discover_existing_databases(
        self, instructions: NotionProvisioningInstructions
    ) -> Dict[str, str]:
        if not self.config.reuse_existing_databases:
            return {}

        client = self._resolve_composio_client()
        if client:
            handler = getattr(client, "discover_databases", None)
            if callable(handler):
                response = handler(
                    workspace=instructions.workspace,
                    schema=instructions.schema,
                    schema_name=instructions.schema_name,
                )
                if isinstance(response, Mapping):
                    return {
                        key: value
                        for key, value in response.items()
                        if key in {"planner", "mirror"} and isinstance(value, str)
                    }

        return self._discover_via_notion_api(instructions)

    def _discover_via_notion_api(
        self, instructions: NotionProvisioningInstructions
    ) -> Dict[str, str]:
        if not instructions.schema_name:
            return {}

        payload = {
            "query": instructions.schema_name,
            "filter": {"property": "object", "value": "database"},
        }
        response = self.session.post(
            "https://api.notion.com/v1/search",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        hits = data.get("results", []) if isinstance(data, Mapping) else []
        database_ids: Dict[str, str] = {}
        for item in hits:
            if not isinstance(item, Mapping):
                continue
            title = self._extract_title(item.get("title"))
            database_id = item.get("id")
            if not title or not isinstance(database_id, str):
                continue
            if "planner" in title.lower():
                database_ids.setdefault("planner", database_id)
            if "mirror" in title.lower():
                database_ids.setdefault("mirror", database_id)

        return database_ids

    def _create_missing_databases(
        self,
        instructions: NotionProvisioningInstructions,
        keys: Iterable[str],
    ) -> Dict[str, str]:
        client = self._resolve_composio_client()
        if client:
            creator = getattr(client, "create_databases", None)
            if callable(creator):
                response = creator(
                    workspace=instructions.workspace,
                    schema=instructions.schema,
                    schema_name=instructions.schema_name,
                    databases=list(keys),
                )
                if isinstance(response, Mapping):
                    created: Dict[str, str] = {}
                    for key in keys:
                        value = response.get(key)
                        if isinstance(value, str):
                            created[key] = value
                    if created:
                        return created

        created = {}
        for key in keys:
            database_id = self._create_database_via_notion_api(instructions, key)
            if database_id:
                created[key] = database_id
        return created

    def _create_database_via_notion_api(
        self, instructions: NotionProvisioningInstructions, role: str
    ) -> Optional[str]:
        parent = instructions.workspace
        if not parent:
            return None

        payload = {
            "parent": {"type": "workspace", "workspace": True},
            "title": [
                {
                    "type": "text",
                    "text": {"content": f"{instructions.schema_name or 'Planner'} - {role.title()}"},
                }
            ],
            "properties": instructions.schema or {},
        }

        response = self.session.post(
            "https://api.notion.com/v1/databases",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        database_id = data.get("id") if isinstance(data, Mapping) else None
        return database_id if isinstance(database_id, str) else None

    # Utilities ---------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_token}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _extract_title(value: Optional[Iterable[Mapping[str, object]]]) -> str:
        if not value:
            return ""
        for part in value:
            if not isinstance(part, Mapping):
                continue
            text = part.get("plain_text") or part.get("text")
            if isinstance(text, Mapping):
                text = text.get("content")
            if isinstance(text, str):
                return text
        return ""

    # Composio helper utilities ---------------------------------------

    def _resolve_composio_client(self) -> Optional[object]:
        """Return the composio client, loading it from an orchestrator if required."""

        if not self._resolved_composio_client_initialized:
            self._resolved_composio_client = (
                self._provided_composio_client or self._lookup_orchestrator_assistant()
            )
            self._resolved_composio_client_initialized = True

        return self._resolved_composio_client

    def _lookup_orchestrator_assistant(self) -> Optional[object]:
        """Ask an orchestrator for the composio assistant if one is configured."""

        slug = self.config.composio_assistant_slug
        if not slug or not self.orchestrator:
            return None

        lookup_methods = (
            "get_assistant",
            "get_or_create_assistant",
            "ensure_assistant",
            "load_assistant",
            "resolve_assistant",
            "fetch_assistant",
        )

        for method_name in lookup_methods:
            handler = getattr(self.orchestrator, method_name, None)
            if not callable(handler):
                continue
            for call_kwargs in (
                {},
                {"slug": slug},
                {"assistant": slug},
                {"assistant_id": slug},
                {"assistant_slug": slug},
                {"name": slug},
                {"id": slug},
            ):
                try:
                    assistant = handler(slug, **call_kwargs)
                except TypeError:
                    try:
                        assistant = handler(**call_kwargs)
                    except TypeError:
                        continue
                if assistant:
                    return assistant

        assistants = getattr(self.orchestrator, "assistants", None)
        if isinstance(assistants, Mapping):
            assistant = assistants.get(slug) or assistants.get(slug.lower())
            if assistant:
                return assistant

        return None

