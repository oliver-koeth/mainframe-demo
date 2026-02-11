# BANKACCT Backend

## Setup

```bash
poetry install
```

## Run

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

## Scheduled Tasks

The API ships with a default heartbeat task that runs every 5 minutes and writes logs to
`output/backend/logs/<task-id>/<execution-id>.log`.
You can also create tasks with function `monthend_interest` to run the migrated COBOL month-end
interest batch flow; its execution log preserves the original console output lines.

Endpoints:
- `GET /scheduled-tasks`
- `POST /scheduled-tasks`
- `GET /scheduled-tasks/{id}`
- `PUT /scheduled-tasks/{id}`
- `DELETE /scheduled-tasks/{id}`
- `POST /scheduled-tasks/{id}/run`
- `GET /scheduled-tasks/{id}/executions`
- `GET /scheduled-tasks/{id}/executions/{execution_id}`
- `GET /scheduled-tasks/{id}/executions/{execution_id}/log`
- `GET /scheduled-tasks/{id}/logs`

## Tests

```bash
poetry run pytest
```
