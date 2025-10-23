# Tulio Day Planner Agent

This package coordinates Gmail, Google Calendar, Google Drive, Todoist and
WhatsApp information through Composio MCP tools to prepare a single payload for
Tulio's planner workflow.

## Configuration

Set the following environment variables before running the agent. Multiple
values accept comma separated lists.

| Variable | Description |
| --- | --- |
| `DAY_PLANNER_DRIVE_FOLDER_IDS` | Comma separated Google Drive folder IDs to mirror. |
| `DAY_PLANNER_TODOIST_PROJECT_FILTERS` | Todoist filter expressions used to select planner tasks (e.g. `today`, `p1`). |
| `DAY_PLANNER_WHATSAPP_CHANNEL_IDS` | Comma separated WhatsApp channel IDs for relevant chats. |
| `DAY_PLANNER_GMAIL_LABEL_FILTER` | Optional Gmail label to limit message ingestion. |
| `DAY_PLANNER_CALENDAR_IDS` | Comma separated Google Calendar IDs. Leave empty to use the primary calendar. |

The agent expects a `ToolRunner` compatible object capable of calling the
following Composio MCP tools:

* `google_gmail:list_messages`
* `google_calendar:list_events`
* `google_drive:list_files`
* `todoist:list_tasks`
* `whatsapp:list_channels`
* `whatsapp:list_messages`

### Example `.env`

```
DAY_PLANNER_DRIVE_FOLDER_IDS=drive-folder-123,drive-folder-456
DAY_PLANNER_TODOIST_PROJECT_FILTERS=today,(p1 & overdue)
DAY_PLANNER_WHATSAPP_CHANNEL_IDS=tulio-team,tulio-family
DAY_PLANNER_GMAIL_LABEL_FILTER=INBOX
DAY_PLANNER_CALENDAR_IDS=primary,team-calendar@group.calendar.google.com
```

## Usage

```python
from tulio_day_planner.agent import sync_day_planner
from tulio_day_planner.config import PlannerConfig

planner_payload = sync_day_planner(tool_runner, PlannerConfig.from_env())
```

The returned payload contains raw source documents alongside a set of summary
counts so downstream workflows can quickly gauge the amount of work required for
any given day.
