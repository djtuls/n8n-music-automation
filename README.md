# Tulio Day Planner Agent

An orchestrator-friendly agent that provisions Notion databases on demand and
synchronises Tulio day planner data. The codebase bundles configuration helpers,
a Notion client with automatic discovery/creation logic, and a ready-to-run
facade that wires everything together.

## Key capabilities

- **Automatic provisioning** – Discover or create planner and mirror databases
  when identifiers are absent.
- **Composio integration** – Optionally invoke a Composio MCP assistant directly
  or via an orchestrator hook before falling back to raw Notion HTTP calls.
- **Vault-backed secrets** – Resolve any `vault://` environment placeholders with
  your orchestrator's vault before constructing the client.
- **Turnkey agent** – Use `TulioDayPlannerAgent` for a batteries-included setup
  that handles provisioning, caching, and the default Notion writers.

## Repository layout

- `tulio-day-planner-agent/src/tulio_day_planner/` – Agent implementation,
  configuration utilities, and Notion client wrappers.
- `example.env` – Template for environment variables understood by the agent.
- `agent_builder.json` – Declarative description for platforms that spin up the
  agent automatically.

## Quick start

1. Copy `example.env` to `.env` (or configure the variables inside your
   orchestrator) and fill in:
   - `NOTION_TOKEN` – Integration token for the Notion workspace.
   - Optional planner/mirror database identifiers if they already exist.
   - `NOTION_PROVISIONING_INSTRUCTIONS` – JSON instructions that describe the
     workspace, schema name, and property definitions when IDs are missing.
   - Provisioning flags and optional Composio settings as needed.
2. Install the package in editable mode so your runtime can import it:

   ```bash
   pip install -e tulio-day-planner-agent
   ```

3. Instantiate and run the agent from Python:

   ```python
   from tulio_day_planner import TulioDayPlannerAgent

   agent = TulioDayPlannerAgent.from_environment(orchestrator=my_orchestrator)
   agent.sync(
       planner_entries=[{"properties": {...}}],
       mirror_entries=[{"properties": {...}}],
   )
   ```

The `sync` call automatically ensures the target databases exist, writes planner
pages (creating or updating as required), appends mirror rows, and returns the
resolved database identifiers for reuse.

## Provisioning options

- `NOTION_REUSE_EXISTING_DATABASES` – Attempt discovery before creating
  databases (defaults to `true`).
- `NOTION_CREATE_DATABASES` – Allow automatic creation when databases are
  missing (defaults to `true`).
- `COMPOSIO_ASSISTANT` / `_SLUG` – Identify the Composio assistant managed by
  your orchestrator.
- Any variable may point to `vault://path#field`; pass the orchestrator instance
  into `NotionConfig.from_env` or `TulioDayPlannerAgent.from_environment` so the
  loader can resolve secrets from the vault before use.

## Development

Run a quick syntax check before committing changes:

```bash
python -m compileall tulio-day-planner-agent/src/tulio_day_planner
```
