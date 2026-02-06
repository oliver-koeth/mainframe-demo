from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    Account,
    AccountCreate,
    AccountUpdate,
    AccountsResponse,
    AmountRequest,
    ApplyInterestBatchResult,
    ApplyInterestResult,
    StatementResponse,
    Transaction,
    TransactionCreate,
    TransactionsResponse,
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


def get_storage() -> Storage:
    return app.state.storage


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


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
