"""Configuration helpers for the Tulio day planner Notion integration."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
from typing import Any, Dict, Mapping, Optional


def _optional_env_value(raw: Optional[str]) -> Optional[str]:
    """Return a stripped environment value or ``None`` when empty."""

    if raw is None:
        return None
    value = raw.strip()
    return value or None


@dataclass(frozen=True)
class NotionProvisioningInstructions:
    """Instructions that describe how databases should be provisioned.

    The instructions are intentionally generic so they can be consumed either by
    Composio's MCP interface or directly by a bespoke Notion bootstrapper.
    """

    workspace: Optional[str] = None
    schema_name: Optional[str] = None
    schema: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Optional[str]) -> Optional["NotionProvisioningInstructions"]:
        """Deserialize provisioning instructions from a JSON payload.

        The payload is expected to be a JSON document with optional
        ``workspace`` and ``schema`` keys. A ``schema_name`` key can be supplied
        to provide a human readable identifier. For convenience the keys
        ``name`` and ``properties`` are accepted as aliases.
        """

        if not raw:
            return None

        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:  # pragma: no cover - defensive
            raise ValueError("Invalid Notion provisioning JSON") from exc

        schema = payload.get("schema") or payload.get("properties") or {}
        schema_name = payload.get("schema_name") or payload.get("name")
        workspace = payload.get("workspace") or payload.get("workspace_id")

        if not isinstance(schema, dict):  # pragma: no cover - defensive
            raise ValueError("Notion provisioning schema must be an object")

        return cls(workspace=workspace, schema_name=schema_name, schema=schema)


@dataclass(frozen=True)
class NotionConfig:
    """Configuration container for Notion synchronisation.

    Database identifiers are now optional; when omitted the provisioning layer
    will discover or create the databases according to the supplied
    instructions.
    """

    api_token: str
    planner_database_id: Optional[str] = None
    mirror_database_id: Optional[str] = None
    provisioning: Optional[NotionProvisioningInstructions] = None
    reuse_existing_databases: bool = True
    create_databases_when_missing: bool = True
    composio_assistant_slug: Optional[str] = None

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "NotionConfig":
        """Build a configuration instance from environment variables."""

        def _flag(name: str, default: bool) -> bool:
            value = env.get(name)
            if value is None:
                return default
            return value.strip().lower() in {"1", "true", "yes", "on"}

        provisioning = NotionProvisioningInstructions.from_mapping(
            env.get("NOTION_PROVISIONING_INSTRUCTIONS")
        )

        composio_assistant = (
            _optional_env_value(env.get("COMPOSIO_ASSISTANT"))
            or _optional_env_value(env.get("COMPOSIO_ASSISTANT_SLUG"))
            or _optional_env_value(env.get("COMPOSIO_ASSISTANT_ID"))
        )

        return cls(
            api_token=env["NOTION_TOKEN"],
            planner_database_id=env.get("NOTION_PLANNER_DATABASE_ID"),
            mirror_database_id=env.get("NOTION_MIRROR_DATABASE_ID"),
            provisioning=provisioning,
            reuse_existing_databases=_flag("NOTION_REUSE_EXISTING_DATABASES", True),
            create_databases_when_missing=_flag("NOTION_CREATE_DATABASES", True),
            composio_assistant_slug=composio_assistant,
        )

    def with_database_ids(self, *, planner: Optional[str], mirror: Optional[str]) -> "NotionConfig":
        """Return a copy with updated database identifiers."""

        return replace(self, planner_database_id=planner, mirror_database_id=mirror)

    @property
    def requires_provisioning(self) -> bool:
        """Indicate whether provisioning logic must run before a sync."""

        missing_planner = not self.planner_database_id
        missing_mirror = not self.mirror_database_id
        return (missing_planner or missing_mirror) and self.create_databases_when_missing

