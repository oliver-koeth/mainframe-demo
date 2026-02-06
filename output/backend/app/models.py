from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

MONEY_QUANT = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


BASE_CONFIG = ConfigDict(extra="forbid", json_encoders={Decimal: lambda v: str(v)})


class AccountBase(BaseModel):
    model_config = BASE_CONFIG

    name: str = Field(min_length=1, max_length=30)
    balance: Decimal = Field(ge=0)
    account_type: str = Field(min_length=1, max_length=1)

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in {"S", "C"}:
            raise ValueError("account_type must be 'S' or 'C'")
        return value

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("balance must be non-negative")
        return quantize_money(value)


class AccountCreate(AccountBase):
    account_id: str = Field(min_length=1, max_length=10)

    @field_validator("account_id")
    @classmethod
    def validate_account_id(cls, value: str) -> str:
        return value.strip()


class AccountUpdate(AccountBase):
    pass


class Account(AccountBase):
    account_id: str


class AmountRequest(BaseModel):
    model_config = BASE_CONFIG

    amount: Decimal = Field(gt=0)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return quantize_money(value)


class TransactionBase(BaseModel):
    model_config = BASE_CONFIG

    account_id: str = Field(min_length=1, max_length=10)
    transaction_type: str = Field(min_length=1, max_length=1)
    amount: Decimal = Field(gt=0)
    date: Optional[str] = Field(default=None, min_length=10, max_length=10)
    time: Optional[str] = Field(default=None, min_length=8, max_length=8)

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in {"D", "W", "I"}:
            raise ValueError("transaction_type must be D, W, or I")
        return value

    @field_validator("account_id")
    @classmethod
    def validate_transaction_account_id(cls, value: str) -> str:
        return value.strip()

    @field_validator("amount")
    @classmethod
    def validate_transaction_amount(cls, value: Decimal) -> Decimal:
        return quantize_money(value)


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    transaction_id: str


class StatementResponse(BaseModel):
    account_id: str
    transactions: list[Transaction]


class AccountsResponse(BaseModel):
    accounts: list[Account]


class TransactionsResponse(BaseModel):
    transactions: list[Transaction]


class ApplyInterestResult(BaseModel):
    account_id: str
    interest_amount: Decimal
    new_balance: Decimal


class ApplyInterestBatchResult(BaseModel):
    applied_count: int
    total_interest: Decimal
    results: list[ApplyInterestResult]
