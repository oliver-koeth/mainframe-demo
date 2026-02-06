from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Optional

from .models import Account, Transaction, quantize_money

SCHEMA_VERSION = 1


class LockTimeoutError(RuntimeError):
    pass


@dataclass
class StoreData:
    accounts: list[Account]
    transactions: list[Transaction]


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
            self._write_raw({"schema_version": SCHEMA_VERSION, "accounts": [], "transactions": []})

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
        return StoreData(accounts=accounts, transactions=transactions)

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
