from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional

from .models import (
    Account,
    AccountCreate,
    AccountUpdate,
    ApplyInterestBatchResult,
    ApplyInterestResult,
    Transaction,
    TransactionCreate,
    quantize_money,
)
from .storage import Storage

INTEREST_RATE = Decimal("0.02")
STATEMENT_LIMIT = 5


class DomainError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def now_date_time() -> tuple[str, str]:
    now = datetime.now()
    date = now.strftime("%Y/%m/%d")
    time = now.strftime("%H:%M:%S")
    return date, time


def create_account(storage: Storage, payload: AccountCreate) -> tuple[Account, bool]:
    account = Account(
        account_id=payload.account_id,
        name=payload.name,
        balance=payload.balance,
        account_type=payload.account_type,
    )
    exists = storage.get_account(account.account_id) is not None
    storage.upsert_account(account)
    return account, exists


def update_account(storage: Storage, account_id: str, payload: AccountUpdate) -> Account:
    existing = storage.get_account(account_id)
    if not existing:
        raise DomainError("account not found", status_code=404)
    updated = Account(
        account_id=account_id,
        name=payload.name,
        balance=payload.balance,
        account_type=payload.account_type,
    )
    storage.upsert_account(updated)
    return updated


def delete_account(storage: Storage, account_id: str) -> None:
    if not storage.delete_account(account_id):
        raise DomainError("account not found", status_code=404)


def deposit(storage: Storage, account_id: str, amount: Decimal) -> tuple[Account, Transaction]:
    account = storage.get_account(account_id)
    if not account:
        raise DomainError("account not found", status_code=404)
    new_balance = quantize_money(account.balance + amount)
    updated = storage.update_account_balance(account_id, new_balance)
    date, time = now_date_time()
    transaction = Transaction(
        transaction_id=str(uuid.uuid4()),
        account_id=account_id,
        transaction_type="D",
        amount=amount,
        date=date,
        time=time,
    )
    storage.append_transaction(transaction)
    return updated, transaction


def withdraw(storage: Storage, account_id: str, amount: Decimal) -> tuple[Account, Transaction]:
    account = storage.get_account(account_id)
    if not account:
        raise DomainError("account not found", status_code=404)
    if account.balance < amount:
        raise DomainError("insufficient funds", status_code=400)
    new_balance = quantize_money(account.balance - amount)
    updated = storage.update_account_balance(account_id, new_balance)
    date, time = now_date_time()
    transaction = Transaction(
        transaction_id=str(uuid.uuid4()),
        account_id=account_id,
        transaction_type="W",
        amount=amount,
        date=date,
        time=time,
    )
    storage.append_transaction(transaction)
    return updated, transaction


def apply_interest_for_account(storage: Storage, account_id: str) -> ApplyInterestResult:
    account = storage.get_account(account_id)
    if not account:
        raise DomainError("account not found", status_code=404)
    if account.account_type != "S":
        raise DomainError("interest applies only to savings accounts", status_code=400)
    interest_amount = quantize_money(account.balance * INTEREST_RATE)
    new_balance = quantize_money(account.balance + interest_amount)
    storage.update_account_balance(account_id, new_balance)
    date, time = now_date_time()
    transaction = Transaction(
        transaction_id=str(uuid.uuid4()),
        account_id=account_id,
        transaction_type="I",
        amount=interest_amount,
        date=date,
        time=time,
    )
    storage.append_transaction(transaction)
    return ApplyInterestResult(
        account_id=account_id,
        interest_amount=interest_amount,
        new_balance=new_balance,
    )


def apply_interest_all(storage: Storage) -> ApplyInterestBatchResult:
    accounts = storage.list_accounts()
    results: list[ApplyInterestResult] = []
    total_interest = Decimal("0.00")
    for account in accounts:
        if account.account_type != "S":
            continue
        interest_amount = quantize_money(account.balance * INTEREST_RATE)
        new_balance = quantize_money(account.balance + interest_amount)
        storage.update_account_balance(account.account_id, new_balance)
        date, time = now_date_time()
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            account_id=account.account_id,
            transaction_type="I",
            amount=interest_amount,
            date=date,
            time=time,
        )
        storage.append_transaction(transaction)
        results.append(
            ApplyInterestResult(
                account_id=account.account_id,
                interest_amount=interest_amount,
                new_balance=new_balance,
            )
        )
        total_interest += interest_amount
    return ApplyInterestBatchResult(
        applied_count=len(results),
        total_interest=quantize_money(total_interest),
        results=results,
    )


def list_statement(storage: Storage, account_id: str) -> list[Transaction]:
    transactions = storage.list_transactions(account_id=account_id)
    return transactions[:STATEMENT_LIMIT]


def create_transaction(storage: Storage, payload: TransactionCreate) -> Transaction:
    account = storage.get_account(payload.account_id)
    if not account:
        raise DomainError("account not found", status_code=404)

    date = payload.date
    time = payload.time
    if not date or not time:
        date, time = now_date_time()

    if payload.transaction_type == "D":
        updated = quantize_money(account.balance + payload.amount)
        storage.update_account_balance(account.account_id, updated)
    elif payload.transaction_type == "W":
        if account.balance < payload.amount:
            raise DomainError("insufficient funds", status_code=400)
        updated = quantize_money(account.balance - payload.amount)
        storage.update_account_balance(account.account_id, updated)
    elif payload.transaction_type == "I":
        if account.account_type != "S":
            raise DomainError("interest applies only to savings accounts", status_code=400)
        updated = quantize_money(account.balance + payload.amount)
        storage.update_account_balance(account.account_id, updated)
    else:
        raise DomainError("invalid transaction type", status_code=400)

    transaction = Transaction(
        transaction_id=str(uuid.uuid4()),
        account_id=payload.account_id,
        transaction_type=payload.transaction_type,
        amount=payload.amount,
        date=date,
        time=time,
    )
    storage.append_transaction(transaction)
    return transaction
