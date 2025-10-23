# Tulio Day Planner Agent

This package defines a portable automation agent that synchronizes Gmail messages, Google Calendar events, and Notion databases to generate a daily executive dashboard for Tulio Ferro.  It is intended to be imported into OpenAI Agent Builder, LangChain, or a similar orchestration platform.

## Overview

The agent performs four primary responsibilities:

1. **Gmail ingestion** – Fetches recent messages, classifies them as tasks, follow-ups, meetings, or informational updates, and extracts metadata such as due dates and participants.
2. **Calendar ingestion** – Collects events for the current and following day, resolving overlaps and identifying travel gaps.
3. **Notion synchronization** – Mirrors every actionable item in structured Notion databases and produces a single "Day Planner" page per date.
4. **Summary generation** – Produces concise bullet lists for new emails, meetings, tasks due, and pending follow-ups.

## Repository Structure

```
tulio-day-planner-agent/
├── agent_builder.json          # Importable agent definition (sanitized)
├── example.env                 # Environment variable template
├── README.md                   # This file
└── src/
    └── tulio_day_planner/
        ├── __init__.py
        ├── agent.py            # High-level orchestration logic
        ├── config.py           # Environment + Notion schema definitions
        └── clients/
            ├── calendar.py
            ├── gmail.py
            └── notion.py
```

## Usage

1. Duplicate `example.env` to `.env` and populate the real credentials (OAuth client, refresh token, Notion integration token, database IDs).
2. Share the three Notion databases with your integration.
3. Install dependencies and run the sync entrypoint:

```bash
python -m tulio_day_planner.agent
```

## Notion Database IDs

Update the following environment variables with the production IDs that have already been provisioned:

- `NOTION_DB_PLANNER=a1979e9c36e64398883d802ecb850d19`
- `NOTION_DB_MIRROR=a6e1faea83564452990da1aeed105179`
- `NOTION_DB_LOG=b7636cbe881d4308bcd84bb9318379e0`

Replace the placeholder values for OAuth credentials and tokens with live secrets before deploying the agent.

## Importing into Agent Builder

- Upload `agent_builder.json` into OpenAI Agent Builder (or adapt it for LangChain by converting the tool configuration to Python code).
- Attach a scheduler that triggers the `sync_day_planner` action at 07:00 local time or when a manual `/sync-now` command is received.

For more details on the workflow, refer to the inline documentation within `src/tulio_day_planner`.
