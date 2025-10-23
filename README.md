# n8n-music-automation

Automated music file processing workflow: Google Drive → n8n → Notion. Extracts metadata,
transcribes lyrics, detects profanity, translates, and searches charts.

## Tulio day planner agent

The `tulio-day-planner-agent` directory contains an experimental agent that syncs day
planner tasks into Notion. The agent can now provision the Notion databases it
needs automatically by talking to Composio's MCP or by falling back to the Notion
HTTP API.

### Notion provisioning flow

1. Configure the Notion integration token in `NOTION_TOKEN`. When the value is
   stored in an orchestrator-managed vault you can reference it with a
   `vault://` URI (see below).
2. Supply database identifiers (`NOTION_PLANNER_DATABASE_ID` and
   `NOTION_MIRROR_DATABASE_ID`) if you already created them.
3. When identifiers are missing, provide a JSON payload in
   `NOTION_PROVISIONING_INSTRUCTIONS` that describes the workspace and target
   schema. Example:

   ```json
   {
     "workspace": "workspace-id-or-name",
     "schema_name": "Tulio Day Planner",
     "schema": {
       "Name": {"title": {}},
       "Status": {"select": {"options": [{"name": "To Do"}, {"name": "Done"}]}}
     }
   }
   ```

4. Toggle whether existing databases should be reused with
   `NOTION_REUSE_EXISTING_DATABASES=true|false` (defaults to `true`).
5. Toggle automatic database creation via `NOTION_CREATE_DATABASES=true|false`
   (defaults to `true`).
6. Optionally attach a Composio MCP client: when present, the agent will call
   `discover_databases` and `create_databases`. Otherwise the Notion REST API is
   used directly. If you rely on a Composio orchestrator to manage assistants,
   set `COMPOSIO_ASSISTANT` (or `COMPOSIO_ASSISTANT_SLUG`) so the agent can look
   up the assistant automatically.

The resulting database identifiers are cached by the agent so subsequent syncs
reuse the same Notion databases without another discovery round.

#### Using a Composio orchestrator

When the Composio assistant is managed by an orchestrator, pass the orchestrator
instance into `NotionClient` and set `COMPOSIO_ASSISTANT` (or
`COMPOSIO_ASSISTANT_SLUG`). The client will query the orchestrator for an
assistant that exposes the `discover_databases`/`create_databases` actions before
provisioning Notion. This lets existing orchestration setups continue to manage
connectors without manual wiring inside the planner agent.

#### Loading secrets from an orchestrator vault

Set environment variables to a `vault://path#field` (or `vault://path:field`)
placeholder to load their values from an orchestrator-managed vault. The
configuration loader will ask the orchestrator (or its `vault` attribute) for
the referenced secret before provisioning Notion. Example:

```bash
NOTION_TOKEN=vault://notion/integration#token
NOTION_PROVISIONING_INSTRUCTIONS=vault://tulio/planner#schema
```

When secrets are resolved through the vault you must call
`NotionConfig.from_env(os.environ, orchestrator=my_orchestrator)` so the loader
has access to the vault APIs. If no orchestrator is provided the agent will
raise an error as soon as it encounters a `vault://` reference.

### Sync pipeline

`PlannerSyncPipeline` always ensures the planner and mirror database identifiers
are resolved before attempting to write data. Writers are passed the resolved IDs
so they can create planner pages and mirror entries.

## Development

Update `example.env` with your configuration choices and copy it to `.env` to run
locally. See `agent_builder.json` for a full agent definition that includes the
new provisioning flags.
