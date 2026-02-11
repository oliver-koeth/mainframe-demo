CODEX Migration Prompt — Scheduled Tasks UI + APScheduler Backend

Use the existing project in `output/` as the base. Implement a Scheduled Tasks feature spanning FastAPI + Angular. Store task metadata and executions in the existing JSON storage with atomic writes and lock. Use APScheduler for execution. Add tests and update docs as described below.

Goal
- Add a Scheduled Tasks management UI (CRUD) and backend endpoints.
- Use APScheduler for actual scheduling/execution.
- Persist tasks and execution history in the established JSON store.
- Provide a log viewer for per‑execution log files.
- Ship a default “heartbeat” task that runs every 5 minutes.

Backend requirements (FastAPI)
- Add APScheduler as a dependency (Poetry).
- Initialize APScheduler on app startup; shut down gracefully on app stop.
- Use 5‑field cron syntax (minute hour day month weekday).
- Data model (persisted in store.json):
  - Task: id (UUID, server‑generated), display_name, function_name, cron, enabled, created_at, updated_at.
  - Execution: id (UUID), task_id, status, started_at, finished_at, log_path.
- Logs stored at `output/backend/logs/<task-id>/<execution-id>.log`.
- Retention: keep last 50 executions per task; purge older metadata and delete corresponding log files.
- Heartbeat task:
  - Function name `heartbeat`.
  - Cron: every 5 minutes.
  - Writes “Hello Heartbeat” to console and its per‑execution log.
- Validation:
  - display_name required, function_name required.
  - cron validated via APScheduler cron trigger parsing (5‑field).
  - Reject duplicate task IDs (409).
- API endpoints:
  - Tasks:
    - `GET /scheduled-tasks`
    - `POST /scheduled-tasks`
    - `GET /scheduled-tasks/{id}`
    - `PUT /scheduled-tasks/{id}`
    - `DELETE /scheduled-tasks/{id}`
  - Executions:
    - `GET /scheduled-tasks/{id}/executions`
    - `GET /scheduled-tasks/{id}/executions/{execution_id}`
  - Logs:
    - `GET /scheduled-tasks/{id}/executions/{execution_id}/log` (returns plain text)

Frontend requirements (Angular)
- Add a route: `scheduled-tasks`.
- List view: tasks table with enabled status, cron, last run.
- Create/Edit form: display name, technical name (function name), cron string, enabled toggle.
- Cron wizard: simple UI to build 5‑field cron (interval, hourly, daily, weekly, monthly) and populate the cron input.
- Task detail: executions list; clicking an execution opens a small log viewer panel with the log contents.
- Basic validation: required fields, cron format check, enabled toggle.

Testing
- Backend pytest:
  - CRUD for tasks.
  - Cron validation errors.
  - Heartbeat run: creates execution + log.
  - Retention keeps last 50; older logs are removed.
  - Log fetch endpoint returns expected text.
- Frontend + Playwright:
  - Create task via wizard.
  - View executions and open log.
  - Delete task.

Docs
- Update API docs and any output docs to include scheduled task endpoints and UI route.
- Add a “scheduled tasks” section in any README under `output/` that describes running and using the feature.

Constraints
- Use the existing JSON storage mechanism with atomic write + lock; do not introduce a database.
- Keep changes within `output/` only.
- Do not modify `_legacy` or `skills`.
