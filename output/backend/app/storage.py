from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Optional

from .models import (
    Account,
    ScheduledTask,
    ScheduledTaskExecution,
    Transaction,
    quantize_money,
)

SCHEMA_VERSION = 1


class LockTimeoutError(RuntimeError):
    pass


@dataclass
class StoreData:
    accounts: list[Account]
    transactions: list[Transaction]
    scheduled_tasks: list[ScheduledTask]
    task_executions: list[ScheduledTaskExecution]


class FileLock:
    def __init__(self, lock_path: Path, timeout_seconds: float = 5.0) -> None:
        self.lock_path = lock_path
        self.timeout_seconds = timeout_seconds
        self._fd: Optional[int] = None

    def __enter__(self) -> "FileLock":
        start = time.time()
        while True:
            try:
                self._fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                if time.time() - start > self.timeout_seconds:
                    raise LockTimeoutError(f"Timed out waiting for lock {self.lock_path}")
                time.sleep(0.05)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._fd is not None:
            os.close(self._fd)
        if self.lock_path.exists():
            self.lock_path.unlink()


def _decimal_from_store(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return quantize_money(value)
    return quantize_money(Decimal(str(value)))


class Storage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock_path = path.with_suffix(path.suffix + ".lock")
        if not self.path.exists():
            self._write_raw(
                {
                    "schema_version": SCHEMA_VERSION,
                    "accounts": [],
                    "transactions": [],
                    "scheduled_tasks": [],
                    "task_executions": [],
                }
            )

    def _read_raw(self) -> dict:
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_raw(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(self.lock_path):
            with tempfile.NamedTemporaryFile("w", delete=False, dir=self.path.parent, encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
                temp_name = handle.name
            os.replace(temp_name, self.path)

    def _deserialize(self, raw: dict) -> StoreData:
        accounts = [Account(
            account_id=item["account_id"],
            name=item["name"],
            balance=_decimal_from_store(item["balance"]),
            account_type=item["account_type"],
        ) for item in raw.get("accounts", [])]
        transactions = [Transaction(
            transaction_id=item["transaction_id"],
            account_id=item["account_id"],
            transaction_type=item["transaction_type"],
            amount=_decimal_from_store(item["amount"]),
            date=item["date"],
            time=item["time"],
        ) for item in raw.get("transactions", [])]
        scheduled_tasks = [
            ScheduledTask(
                id=item["id"],
                display_name=item["display_name"],
                function_name=item["function_name"],
                cron=item["cron"],
                enabled=item["enabled"],
                created_at=item["created_at"],
                updated_at=item["updated_at"],
                last_run=item.get("last_run"),
            )
            for item in raw.get("scheduled_tasks", [])
        ]
        task_executions = [
            ScheduledTaskExecution(
                id=item["id"],
                task_id=item["task_id"],
                status=item["status"],
                started_at=item["started_at"],
                finished_at=item["finished_at"],
                log_path=item["log_path"],
            )
            for item in raw.get("task_executions", [])
        ]
        return StoreData(
            accounts=accounts,
            transactions=transactions,
            scheduled_tasks=scheduled_tasks,
            task_executions=task_executions,
        )

    def _serialize(self, store: StoreData) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "accounts": [
                {
                    "account_id": account.account_id,
                    "name": account.name,
                    "balance": str(account.balance),
                    "account_type": account.account_type,
                }
                for account in store.accounts
            ],
            "transactions": [
                {
                    "transaction_id": txn.transaction_id,
                    "account_id": txn.account_id,
                    "transaction_type": txn.transaction_type,
                    "amount": str(txn.amount),
                    "date": txn.date,
                    "time": txn.time,
                }
                for txn in store.transactions
            ],
            "scheduled_tasks": [
                {
                    "id": task.id,
                    "display_name": task.display_name,
                    "function_name": task.function_name,
                    "cron": task.cron,
                    "enabled": task.enabled,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "last_run": task.last_run,
                }
                for task in store.scheduled_tasks
            ],
            "task_executions": [
                {
                    "id": execution.id,
                    "task_id": execution.task_id,
                    "status": execution.status,
                    "started_at": execution.started_at,
                    "finished_at": execution.finished_at,
                    "log_path": execution.log_path,
                }
                for execution in store.task_executions
            ],
        }

    def load(self) -> StoreData:
        raw = self._read_raw()
        return self._deserialize(raw)

    def save(self, store: StoreData) -> None:
        self._write_raw(self._serialize(store))

    def list_accounts(self) -> list[Account]:
        return list(self.load().accounts)

    def get_account(self, account_id: str) -> Optional[Account]:
        for account in self.load().accounts:
            if account.account_id == account_id:
                return account
        return None

    def upsert_account(self, account: Account) -> Account:
        store = self.load()
        updated = False
        for idx, existing in enumerate(store.accounts):
            if existing.account_id == account.account_id:
                store.accounts[idx] = account
                updated = True
                break
        if not updated:
            store.accounts.append(account)
        self.save(store)
        return account

    def delete_account(self, account_id: str) -> bool:
        store = self.load()
        before = len(store.accounts)
        store.accounts = [acct for acct in store.accounts if acct.account_id != account_id]
        if len(store.accounts) == before:
            return False
        self.save(store)
        return True

    def update_account_balance(self, account_id: str, new_balance: Decimal) -> Account:
        store = self.load()
        for idx, account in enumerate(store.accounts):
            if account.account_id == account_id:
                updated = Account(
                    account_id=account.account_id,
                    name=account.name,
                    balance=quantize_money(new_balance),
                    account_type=account.account_type,
                )
                store.accounts[idx] = updated
                self.save(store)
                return updated
        raise KeyError(account_id)

    def append_transaction(self, transaction: Transaction) -> Transaction:
        store = self.load()
        store.transactions.append(transaction)
        self.save(store)
        return transaction

    def list_transactions(
        self,
        account_id: Optional[str] = None,
        transaction_type: Optional[str] = None,
    ) -> list[Transaction]:
        transactions = self.load().transactions
        results: Iterable[Transaction] = transactions
        if account_id:
            results = [txn for txn in results if txn.account_id == account_id]
        if transaction_type:
            results = [txn for txn in results if txn.transaction_type == transaction_type]
        return list(results)

    def list_scheduled_tasks(self) -> list[ScheduledTask]:
        return list(self.load().scheduled_tasks)

    def get_scheduled_task(self, task_id: str) -> Optional[ScheduledTask]:
        for task in self.load().scheduled_tasks:
            if task.id == task_id:
                return task
        return None

    def upsert_scheduled_task(self, task: ScheduledTask) -> ScheduledTask:
        store = self.load()
        updated = False
        for idx, existing in enumerate(store.scheduled_tasks):
            if existing.id == task.id:
                store.scheduled_tasks[idx] = task
                updated = True
                break
        if not updated:
            store.scheduled_tasks.append(task)
        self.save(store)
        return task

    def delete_scheduled_task(self, task_id: str) -> bool:
        store = self.load()
        before = len(store.scheduled_tasks)
        store.scheduled_tasks = [task for task in store.scheduled_tasks if task.id != task_id]
        if len(store.scheduled_tasks) == before:
            return False
        store.task_executions = [execution for execution in store.task_executions if execution.task_id != task_id]
        self.save(store)
        return True

    def list_task_executions(self, task_id: Optional[str] = None) -> list[ScheduledTaskExecution]:
        executions = self.load().task_executions
        if task_id:
            executions = [execution for execution in executions if execution.task_id == task_id]
        return list(executions)

    def get_task_execution(self, task_id: str, execution_id: str) -> Optional[ScheduledTaskExecution]:
        for execution in self.load().task_executions:
            if execution.task_id == task_id and execution.id == execution_id:
                return execution
        return None

    def append_task_execution(self, execution: ScheduledTaskExecution) -> ScheduledTaskExecution:
        store = self.load()
        store.task_executions.append(execution)
        self.save(store)
        return execution

    def prune_task_executions(self, task_id: str, keep: int = 50) -> list[ScheduledTaskExecution]:
        store = self.load()
        executions = [execution for execution in store.task_executions if execution.task_id == task_id]
        other = [execution for execution in store.task_executions if execution.task_id != task_id]
        executions.sort(key=lambda item: item.started_at, reverse=True)
        kept = executions[:keep]
        removed = executions[keep:]
        store.task_executions = other + kept
        if removed:
            self.save(store)
        return removed
