from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.storage import Storage


def make_client(tmp_path):
    app.state.storage = Storage(tmp_path / "store.json")
    return TestClient(app)


def test_missing_account(tmp_path):
    client = make_client(tmp_path)
    resp = client.get("/accounts/nope")
    assert resp.status_code == 404


def test_duplicate_account_overwrite(tmp_path):
    client = make_client(tmp_path)
    resp = client.post(
        "/accounts",
        json={
            "account_id": "abc123",
            "name": "First",
            "balance": "100.00",
            "account_type": "S",
        },
    )
    assert resp.status_code == 200
    resp = client.post(
        "/accounts",
        json={
            "account_id": "abc123",
            "name": "Second",
            "balance": "250.00",
            "account_type": "C",
        },
    )
    assert resp.status_code == 200
    resp = client.get("/accounts/abc123")
    data = resp.json()
    assert data["name"] == "Second"
    assert data["balance"] == "250.00"
    assert data["account_type"] == "C"


def test_insufficient_funds_block_withdrawal(tmp_path):
    client = make_client(tmp_path)
    client.post(
        "/accounts",
        json={
            "account_id": "acct1",
            "name": "Saver",
            "balance": "10.00",
            "account_type": "S",
        },
    )
    resp = client.post("/accounts/acct1/withdraw", json={"amount": "25.00"})
    assert resp.status_code == 400
    assert "insufficient" in resp.json()["detail"].lower()


def test_bad_transaction_type(tmp_path):
    client = make_client(tmp_path)
    client.post(
        "/accounts",
        json={
            "account_id": "acct2",
            "name": "Checker",
            "balance": "50.00",
            "account_type": "C",
        },
    )
    resp = client.post(
        "/transactions",
        json={
            "account_id": "acct2",
            "transaction_type": "X",
            "amount": "5.00",
        },
    )
    assert resp.status_code == 422
