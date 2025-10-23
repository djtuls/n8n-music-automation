# Implementing the Tulio Day Planner Agent

This guide walks through the concrete steps required to embed the Tulio day planner automation inside your own GPT-style assistant or orchestrated runtime. It focuses on wiring environment configuration, provisioning logic, and sync calls so that your agent can continuously push planner data into Notion.

## 1. Install the package

Install the local package in editable mode so you can iterate quickly:

```bash
pip install -e tulio-day-planner-agent
```

The package exposes the `tulio_day_planner` namespace that contains the configuration helpers, Notion client, sync pipeline, and the turnkey agent facade.

## 2. Prepare environment variables (or vault secrets)

Populate the variables documented in `example.env` and the project README. When running under an orchestrator, you can replace sensitive values with `vault://` references—`NotionConfig.from_env` will resolve them against the orchestrator's vault automatically.

| Variable | Purpose |
| --- | --- |
| `NOTION_TOKEN` | Integration token for the Notion workspace. |
| `NOTION_PLANNER_DATABASE_ID` / `NOTION_MIRROR_DATABASE_ID` | Optional IDs for existing databases. Leave blank to auto-provision. |
| `NOTION_PROVISIONING_INSTRUCTIONS` | JSON payload describing the workspace, schema name, and database properties. |
| `NOTION_REUSE_EXISTING_DATABASES` | "true"/"false" flag controlling whether discovery happens before creation. |
| `NOTION_CREATE_DATABASES` | "true"/"false" flag controlling whether creation is allowed when databases are missing. |
| `COMPOSIO_ASSISTANT` or `COMPOSIO_ASSISTANT_SLUG` | Name or slug of the Composio assistant that can manage Notion databases. |

## 3. Instantiate configuration and the client

```python
from tulio_day_planner.config import NotionConfig
from tulio_day_planner.notion_client import NotionClient

config = NotionConfig.from_env(os.environ, orchestrator=my_orchestrator)
client = NotionClient(
    config,
    orchestrator=my_orchestrator,
    composio_client=optional_direct_composio_client,
)
```

The client lazily resolves database identifiers by reusing existing IDs, discovering them through the Composio assistant, or creating them via Composio/the Notion REST API when permitted.

## 4. Provision databases and sync content

```python
resolved = client.ensure_databases()

pipeline = PlannerSyncPipeline(client)

pipeline.sync(
    planner_entries=[{"properties": {"Name": {"title": [{"text": {"content": "Plan"}}]}}}],
    mirror_entries=[{"properties": {...}}],
    database_ids=resolved,
)
```

`ensure_databases()` caches the planner and mirror database IDs, so subsequent syncs reuse them without re-provisioning. The pipeline delegates to the default planner and mirror writers.

## 5. Use the turnkey agent for convenience

```python
from tulio_day_planner import TulioDayPlannerAgent

agent = TulioDayPlannerAgent.from_environment(orchestrator=my_orchestrator)
agent.sync(
    planner_entries=[...],
    mirror_entries=[...],
)
```

The facade wraps all configuration, provisioning, and syncing steps in a single method call and returns the resolved database identifiers for further processing if needed.

## 6. Running inside a GPT orchestration platform

1. Register the environment variables in your orchestrator (or reference vault secrets).
2. Deploy a Composio assistant that exposes `discover_databases` and `create_databases` actions aligned with your schema.
3. Ship a thin wrapper that calls `TulioDayPlannerAgent.from_environment` with the orchestrator instance provided by your platform.
4. On each planner update, call `agent.sync(...)` with the computed planner and mirror payloads.

This approach allows the GPT agent to self-provision Notion resources, reuse cached identifiers, and keep future synchronisations fast and reliable.
