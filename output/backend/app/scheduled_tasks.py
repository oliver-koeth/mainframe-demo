from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

from .models import ScheduledTask, ScheduledTaskCreate, ScheduledTaskExecution, ScheduledTaskUpdate
from .services import DomainError
from .storage import Storage
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def validate_cron(cron: str) -> None:
    try:
        CronTrigger.from_crontab(cron)
    except Exception as exc:  # pragma: no cover - exact exception varies
        raise DomainError("invalid cron expression", status_code=400) from exc


def create_task(storage: Storage, payload: ScheduledTaskCreate) -> ScheduledTask:
    validate_cron(payload.cron)
    if payload.task_id:
        if storage.get_scheduled_task(payload.task_id):
            raise DomainError("task id already exists", status_code=409)
        task_id = payload.task_id
    else:
        task_id = str(uuid.uuid4())
    timestamp = now_iso()
    task = ScheduledTask(
        id=task_id,
        display_name=payload.display_name,
        function_name=payload.function_name,
        cron=payload.cron,
        enabled=payload.enabled,
        created_at=timestamp,
        updated_at=timestamp,
        last_run=None,
    )
    storage.upsert_scheduled_task(task)
    return task


def update_task(storage: Storage, task_id: str, payload: ScheduledTaskUpdate) -> ScheduledTask:
    existing = storage.get_scheduled_task(task_id)
    if not existing:
        raise DomainError("task not found", status_code=404)
    validate_cron(payload.cron)
    updated = ScheduledTask(
        id=task_id,
        display_name=payload.display_name,
        function_name=payload.function_name,
        cron=payload.cron,
        enabled=payload.enabled,
        created_at=existing.created_at,
        updated_at=now_iso(),
        last_run=existing.last_run,
    )
    storage.upsert_scheduled_task(updated)
    return updated


def delete_task(storage: Storage, task_id: str) -> None:
    if not storage.delete_scheduled_task(task_id):
        raise DomainError("task not found", status_code=404)


def list_tasks_with_last_run(storage: Storage) -> list[ScheduledTask]:
    tasks = storage.list_scheduled_tasks()
    executions = storage.list_task_executions()
    last_run_by_task: dict[str, str] = {}
    for execution in executions:
        last_run_by_task[execution.task_id] = execution.started_at
    results: list[ScheduledTask] = []
    for task in tasks:
        results.append(
            ScheduledTask(
                id=task.id,
                display_name=task.display_name,
                function_name=task.function_name,
                cron=task.cron,
                enabled=task.enabled,
                created_at=task.created_at,
                updated_at=task.updated_at,
                last_run=last_run_by_task.get(task.id),
            )
        )
    return results


class ScheduledTaskManager:
    def __init__(self, storage: Storage, logs_dir: Path) -> None:
        self.storage = storage
        self.logs_dir = logs_dir
        self.scheduler = BackgroundScheduler()
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.scheduler.start()
        self._started = True
        self.sync_jobs()

    def shutdown(self) -> None:
        if not self._started:
            return
        self.scheduler.shutdown(wait=False)
        self._started = False

    def ensure_default_tasks(self) -> None:
        existing = self.storage.list_scheduled_tasks()
        for task in existing:
            if task.function_name == "heartbeat":
                return
        default_task = ScheduledTask(
            id=str(uuid.uuid4()),
            display_name="Heartbeat",
            function_name="heartbeat",
            cron="*/5 * * * *",
            enabled=True,
            created_at=now_iso(),
            updated_at=now_iso(),
            last_run=None,
        )
        self.storage.upsert_scheduled_task(default_task)

    def sync_jobs(self) -> None:
        if not self._started:
            return
        self.scheduler.remove_all_jobs()
        for task in self.storage.list_scheduled_tasks():
            if task.enabled:
                self._schedule_task(task)

    def add_or_update_job(self, task: ScheduledTask) -> None:
        if not self._started:
            return
        if task.enabled:
            self._schedule_task(task)
        else:
            self.remove_job(task.id)

    def remove_job(self, task_id: str) -> None:
        if not self._started:
            return
        try:
            self.scheduler.remove_job(task_id)
        except JobLookupError:
            pass

    def _schedule_task(self, task: ScheduledTask) -> None:
        trigger = CronTrigger.from_crontab(task.cron)
        self.scheduler.add_job(
            self.run_task,
            trigger=trigger,
            id=task.id,
            args=[task.id],
            replace_existing=True,
        )

    def run_task(self, task_id: str) -> Optional[ScheduledTaskExecution]:
        task = self.storage.get_scheduled_task(task_id)
        if not task or not task.enabled:
            return None
        execution_id = str(uuid.uuid4())
        started_at = now_iso()
        task_dir = self.logs_dir / task.id
        task_dir.mkdir(parents=True, exist_ok=True)
        log_path = task_dir / f"{execution_id}.log"
        status = "success"
        log_lines: list[str] = []
        try:
            if task.function_name == "heartbeat":
                message = "Hello Heartbeat"
                print(message)
                log_lines.append(message)
            else:
                raise RuntimeError(f"Unknown function {task.function_name}")
        except Exception as exc:  # pragma: no cover - defensive
            status = "failed"
            log_lines.append(f"Error: {exc}")
        log_text = "\n".join(log_lines)
        log_path.write_text(log_text + "\n", encoding="utf-8")
        finished_at = now_iso()
        execution = ScheduledTaskExecution(
            id=execution_id,
            task_id=task.id,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            log_path=str(log_path),
        )
        self.storage.append_task_execution(execution)
        updated_task = ScheduledTask(
            id=task.id,
            display_name=task.display_name,
            function_name=task.function_name,
            cron=task.cron,
            enabled=task.enabled,
            created_at=task.created_at,
            updated_at=task.updated_at,
            last_run=started_at,
        )
        self.storage.upsert_scheduled_task(updated_task)
        removed = self.storage.prune_task_executions(task.id, keep=50)
        for old in removed:
            try:
                Path(old.log_path).unlink()
            except FileNotFoundError:
                pass
        return execution
