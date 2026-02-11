from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .models import (
    Account,
    AccountCreate,
    AccountUpdate,
    AccountsResponse,
    AmountRequest,
    ApplyInterestBatchResult,
    ApplyInterestResult,
    ScheduledTask,
    ScheduledTaskCreate,
    ScheduledTaskExecution,
    ScheduledTaskExecutionsResponse,
    ScheduledTaskLogItem,
    ScheduledTaskLogsResponse,
    ScheduledTaskUpdate,
    ScheduledTasksResponse,
    StatementResponse,
    Transaction,
    TransactionCreate,
    TransactionsResponse,
)
from .scheduled_tasks import (
    ScheduledTaskManager,
    create_task,
    delete_task,
    list_tasks_with_last_run,
    update_task,
)
from .services import (
    DomainError,
    apply_interest_all,
    apply_interest_for_account,
    create_account,
    create_transaction,
    delete_account,
    deposit,
    list_statement,
    update_account,
    withdraw,
)
from .storage import Storage

app = FastAPI(title="Bank Account API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] ,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"] ,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "store.json"
app.state.storage = Storage(DATA_PATH)
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"


def get_storage() -> Storage:
    return app.state.storage


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def get_scheduler() -> ScheduledTaskManager:
    return app.state.scheduler


@app.on_event("startup")
def on_startup() -> None:
    scheduler = ScheduledTaskManager(get_storage(), LOGS_DIR)
    scheduler.ensure_default_tasks()
    scheduler.start()
    app.state.scheduler = scheduler


@app.on_event("shutdown")
def on_shutdown() -> None:
    scheduler: ScheduledTaskManager = app.state.scheduler
    scheduler.shutdown()


@app.get("/accounts", response_model=AccountsResponse)
def list_accounts() -> AccountsResponse:
    storage = get_storage()
    return AccountsResponse(accounts=storage.list_accounts())


@app.post("/accounts", response_model=Account)
def create_account_route(payload: AccountCreate) -> Account:
    storage = get_storage()
    account, _ = create_account(storage, payload)
    return account


@app.get("/accounts/{account_id}", response_model=Account)
def get_account(account_id: str) -> Account:
    storage = get_storage()
    account = storage.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="account not found")
    return account


@app.put("/accounts/{account_id}", response_model=Account)
def update_account_route(account_id: str, payload: AccountUpdate) -> Account:
    try:
        return update_account(get_storage(), account_id, payload)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.delete("/accounts/{account_id}")
def delete_account_route(account_id: str) -> dict:
    try:
        delete_account(get_storage(), account_id)
        return {"status": "deleted"}
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.post("/accounts/{account_id}/deposit")
def deposit_route(account_id: str, payload: AmountRequest) -> dict:
    try:
        account, transaction = deposit(get_storage(), account_id, payload.amount)
        return {"account": account, "transaction": transaction}
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.post("/accounts/{account_id}/withdraw")
def withdraw_route(account_id: str, payload: AmountRequest) -> dict:
    try:
        account, transaction = withdraw(get_storage(), account_id, payload.amount)
        return {"account": account, "transaction": transaction}
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.post("/accounts/{account_id}/apply-interest", response_model=ApplyInterestResult)
def apply_interest_route(account_id: str) -> ApplyInterestResult:
    try:
        return apply_interest_for_account(get_storage(), account_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.post("/accounts/apply-interest", response_model=ApplyInterestBatchResult)
def apply_interest_all_route() -> ApplyInterestBatchResult:
    return apply_interest_all(get_storage())


@app.get("/accounts/{account_id}/statement", response_model=StatementResponse)
def statement_route(account_id: str) -> StatementResponse:
    storage = get_storage()
    account = storage.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="account not found")
    transactions = list_statement(storage, account_id)
    return StatementResponse(account_id=account_id, transactions=transactions)


@app.post("/transactions", response_model=Transaction)
def create_transaction_route(payload: TransactionCreate) -> Transaction:
    try:
        return create_transaction(get_storage(), payload)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.get("/transactions", response_model=TransactionsResponse)
def list_transactions(
    account_id: Optional[str] = None,
    transaction_type: Optional[str] = Query(default=None, min_length=1, max_length=1),
) -> TransactionsResponse:
    if transaction_type:
        transaction_type = transaction_type.upper()
    transactions = get_storage().list_transactions(
        account_id=account_id,
        transaction_type=transaction_type,
    )
    return TransactionsResponse(transactions=transactions)


@app.get("/transactions/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: str) -> Transaction:
    transactions = get_storage().list_transactions()
    for txn in transactions:
        if txn.transaction_id == transaction_id:
            return txn
    raise HTTPException(status_code=404, detail="transaction not found")


@app.get("/scheduled-tasks", response_model=ScheduledTasksResponse)
def list_scheduled_tasks() -> ScheduledTasksResponse:
    return ScheduledTasksResponse(tasks=list_tasks_with_last_run(get_storage()))


@app.post("/scheduled-tasks", response_model=ScheduledTask)
def create_scheduled_task(payload: ScheduledTaskCreate) -> ScheduledTask:
    try:
        task = create_task(get_storage(), payload)
        get_scheduler().add_or_update_job(task)
        return task
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.get("/scheduled-tasks/{task_id}", response_model=ScheduledTask)
def get_scheduled_task(task_id: str) -> ScheduledTask:
    task = get_storage().get_scheduled_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.put("/scheduled-tasks/{task_id}", response_model=ScheduledTask)
def update_scheduled_task(task_id: str, payload: ScheduledTaskUpdate) -> ScheduledTask:
    try:
        task = update_task(get_storage(), task_id, payload)
        get_scheduler().add_or_update_job(task)
        return task
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.delete("/scheduled-tasks/{task_id}")
def delete_scheduled_task(task_id: str) -> dict:
    try:
        storage = get_storage()
        executions = storage.list_task_executions(task_id=task_id)
        delete_task(storage, task_id)
        get_scheduler().remove_job(task_id)
        for execution in executions:
            try:
                Path(execution.log_path).unlink()
            except FileNotFoundError:
                pass
        return {"status": "deleted"}
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.get("/scheduled-tasks/{task_id}/executions", response_model=ScheduledTaskExecutionsResponse)
def list_task_executions(task_id: str) -> ScheduledTaskExecutionsResponse:
    if not get_storage().get_scheduled_task(task_id):
        raise HTTPException(status_code=404, detail="task not found")
    executions = get_storage().list_task_executions(task_id=task_id)
    return ScheduledTaskExecutionsResponse(executions=executions)


@app.get("/scheduled-tasks/{task_id}/executions/{execution_id}", response_model=ScheduledTaskExecution)
def get_task_execution(task_id: str, execution_id: str) -> ScheduledTaskExecution:
    execution = get_storage().get_task_execution(task_id, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="execution not found")
    return execution


@app.post("/scheduled-tasks/{task_id}/run", response_model=ScheduledTaskExecution)
def run_task_now(task_id: str) -> ScheduledTaskExecution:
    if not get_storage().get_scheduled_task(task_id):
        raise HTTPException(status_code=404, detail="task not found")
    execution = get_scheduler().run_task(task_id)
    if not execution:
        raise HTTPException(status_code=400, detail="task disabled or unavailable")
    return execution


@app.get("/scheduled-tasks/{task_id}/logs", response_model=ScheduledTaskLogsResponse)
def list_task_logs(task_id: str) -> ScheduledTaskLogsResponse:
    if not get_storage().get_scheduled_task(task_id):
        raise HTTPException(status_code=404, detail="task not found")
    task_dir = LOGS_DIR / task_id
    if not task_dir.exists():
        return ScheduledTaskLogsResponse(logs=[])
    logs: list[ScheduledTaskLogItem] = []
    for path in sorted(task_dir.glob("*.log"), key=lambda item: item.stat().st_mtime, reverse=True):
        execution_id = path.stem
        logs.append(ScheduledTaskLogItem(execution_id=execution_id, log_path=str(path)))
    return ScheduledTaskLogsResponse(logs=logs)


@app.get(
    "/scheduled-tasks/{task_id}/executions/{execution_id}/log",
    response_class=PlainTextResponse,
)
def get_task_execution_log(task_id: str, execution_id: str) -> PlainTextResponse:
    execution = get_storage().get_task_execution(task_id, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="execution not found")
    try:
        text = Path(execution.log_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="log not found")
    return PlainTextResponse(text)
