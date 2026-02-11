# Scheduled Tasks

## API Endpoints

Tasks
- `GET /scheduled-tasks`
- `POST /scheduled-tasks`
- `GET /scheduled-tasks/{id}`
- `PUT /scheduled-tasks/{id}`
- `DELETE /scheduled-tasks/{id}`
- `POST /scheduled-tasks/{id}/run`

Executions
- `GET /scheduled-tasks/{id}/executions`
- `GET /scheduled-tasks/{id}/executions/{execution_id}`
- `GET /scheduled-tasks/{id}/executions/{execution_id}/log`
- `GET /scheduled-tasks/{id}/logs`

## UI Route

- `/scheduled-tasks`

## Logs

Execution logs are written to `output/backend/logs/<task-id>/<execution-id>.log`.

## Default Task

A default `heartbeat` task runs every 5 minutes and writes “Hello Heartbeat” to the log.
