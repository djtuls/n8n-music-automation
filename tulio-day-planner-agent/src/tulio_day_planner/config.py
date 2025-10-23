"""Configuration helpers for the Tulio day planner Notion integration."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
from typing import Any, Dict, Mapping, Optional


def _extract_secret_value(result: Any, key: Optional[str]) -> Optional[str]:
    """Attempt to extract a textual secret from a vault response."""

    if result is None:
        return None

    if isinstance(result, str):
        return result

    if key and isinstance(result, Mapping):
        candidate = result.get(key)
        if isinstance(candidate, str):
            return candidate

    attribute_candidates = [key, "value", "secret", "secret_value", "data", "content"]
    for attr in attribute_candidates:
        if not attr:
            continue
        if isinstance(result, Mapping):
            candidate = result.get(attr)
        else:
            candidate = getattr(result, attr, None)
        if isinstance(candidate, str):
            return candidate
        if isinstance(candidate, Mapping):
            nested = _extract_secret_value(candidate, None)
            if isinstance(nested, str):
                return nested

    return None


def _fetch_secret_from_source(
    source: object, reference: str, path: str, key: Optional[str]
) -> Optional[str]:
    """Best-effort secret resolution against a single source object."""

    if source is None:
        return None

    lookup_candidates = [candidate for candidate in {reference, path} if candidate]

    if isinstance(source, Mapping):
        for candidate in lookup_candidates:
            candidate_value = source.get(candidate)
            secret = _extract_secret_value(candidate_value, key)
            if secret:
                return secret
        if path and "/" in path:
            current: Any = source
            for part in path.split("/"):
                if not isinstance(current, Mapping):
                    break
                current = current.get(part)
            secret = _extract_secret_value(current, key)
            if secret:
                return secret

    method_names = (
        "get_secret",
        "fetch_secret",
        "read_secret",
        "resolve_secret",
        "load_secret",
        "secret",
        "get",
        "read",
        "lookup",
        "retrieve_secret",
    )

    for method_name in method_names:
        handler = getattr(source, method_name, None)
        if not callable(handler):
            continue
        for candidate in lookup_candidates or [None]:
            call_args = ()
            if candidate is not None:
                call_args = (candidate,)
            try:
                result = handler(*call_args)
            except TypeError:
                kwarg_candidates = (
                    {"name": candidate} if candidate is not None else {},
                    {"key": candidate} if candidate is not None else {},
                    {"path": candidate} if candidate is not None else {},
                    {"secret": candidate} if candidate is not None else {},
                )
                for kwargs in kwarg_candidates:
                    if not kwargs:
                        continue
                    try:
                        result = handler(**kwargs)
                    except TypeError:
                        continue
                    else:
                        break
                else:
                    continue
            secret = _extract_secret_value(result, key)
            if secret:
                return secret

    for candidate in lookup_candidates:
        try:
            result = source[candidate]  # type: ignore[index]
        except (TypeError, KeyError, AttributeError):
            continue
        secret = _extract_secret_value(result, key)
        if secret:
            return secret

    return None


def _resolve_vault_reference(
    value: Optional[str],
    orchestrator: Optional[object],
    *,
    env_name: str,
) -> Optional[str]:
    """Resolve ``vault://`` references through the provided orchestrator."""

    if not value or not value.startswith("vault://"):
        return value

    if orchestrator is None:
        raise RuntimeError(
            f"{env_name} references an orchestrator vault secret but no orchestrator was supplied."
        )

    reference = value[len("vault://") :]
    reference = reference.strip()
    if not reference:
        raise RuntimeError(f"Vault reference for {env_name} is empty")

    path, _, key = reference.partition("#")
    if not key and ":" in path:
        path, key = path.split(":", 1)
    path = path.strip()
    key = key.strip() if key else None

    sources = []
    vault = getattr(orchestrator, "vault", None)
    if vault is not None:
        sources.append(vault)
    sources.append(orchestrator)

    for source in sources:
        secret = _fetch_secret_from_source(source, reference, path, key)
        if secret:
            return secret.strip()

    raise RuntimeError(f"Unable to resolve vault secret '{reference}' for {env_name}")


def _env_or_vault_value(
    env: Mapping[str, str],
    name: str,
    *,
    orchestrator: Optional[object],
    required: bool = False,
) -> Optional[str]:
    """Fetch an environment value, resolving orchestrator vault placeholders."""

    value = _optional_env_value(env.get(name))
    if value is None:
        placeholder_keys = [
            f"{name}_VAULT",
            f"{name}_VAULT_PATH",
            f"{name}_VAULT_SECRET",
            f"{name}_SECRET",
        ]
        for key in placeholder_keys:
            value = _optional_env_value(env.get(key))
            if value:
                break

    value = _resolve_vault_reference(value, orchestrator, env_name=name)

    if required and not value:
        raise KeyError(name)

    return value


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
    def from_env(
        cls, env: Mapping[str, str], *, orchestrator: Optional[object] = None
    ) -> "NotionConfig":
        """Build a configuration instance from environment variables.

        When values include ``vault://`` placeholders, the optional
        ``orchestrator`` is queried (and its ``vault`` attribute, when present)
        to resolve those secrets before creating the configuration object.
        """

        def _flag(name: str, default: bool) -> bool:
            value = env.get(name)
            if value is None:
                return default
            return value.strip().lower() in {"1", "true", "yes", "on"}

        provisioning_raw = _env_or_vault_value(
            env, "NOTION_PROVISIONING_INSTRUCTIONS", orchestrator=orchestrator
        )
        provisioning = NotionProvisioningInstructions.from_mapping(provisioning_raw)

        composio_assistant = (
            _env_or_vault_value(env, "COMPOSIO_ASSISTANT", orchestrator=orchestrator)
            or _env_or_vault_value(
                env, "COMPOSIO_ASSISTANT_SLUG", orchestrator=orchestrator
            )
            or _env_or_vault_value(
                env, "COMPOSIO_ASSISTANT_ID", orchestrator=orchestrator
            )
        )

        return cls(
            api_token=_env_or_vault_value(
                env, "NOTION_TOKEN", orchestrator=orchestrator, required=True
            ),
            planner_database_id=_env_or_vault_value(
                env, "NOTION_PLANNER_DATABASE_ID", orchestrator=orchestrator
            ),
            mirror_database_id=_env_or_vault_value(
                env, "NOTION_MIRROR_DATABASE_ID", orchestrator=orchestrator
            ),
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

