from decimal import Decimal

from app.services import apply_interest_for_account, list_statement
from app.storage import Storage
from app.models import Account, Transaction


def test_interest_only_savings(tmp_path):
    storage = Storage(tmp_path / "store.json")
    storage.upsert_account(Account(account_id="s1", name="Saver", balance=Decimal("100.00"), account_type="S"))
    storage.upsert_account(Account(account_id="c1", name="Checker", balance=Decimal("100.00"), account_type="C"))

    result = apply_interest_for_account(storage, "s1")
    assert result.interest_amount == Decimal("2.00")

    try:
        apply_interest_for_account(storage, "c1")
        assert False, "Expected error for checking account"
    except Exception as exc:
        assert "savings" in str(exc).lower()


def test_statement_limit(tmp_path):
    storage = Storage(tmp_path / "store.json")
    storage.upsert_account(Account(account_id="acct", name="User", balance=Decimal("0.00"), account_type="S"))
    for idx in range(10):
        storage.append_transaction(
            Transaction(
                transaction_id=f"t{idx}",
                account_id="acct",
                transaction_type="D",
                amount=Decimal("1.00"),
                date="2025/01/01",
                time="00:00:00",
            )
        )
    statement = list_statement(storage, "acct")
    assert len(statement) == 5
    assert statement[0].transaction_id == "t0"
