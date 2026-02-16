from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.models import Account, ScheduledTaskCreate
from app.scheduled_tasks import ScheduledTaskManager, create_task
from app.storage import Storage


def make_client(tmp_path: Path) -> TestClient:
    main.LOGS_DIR = tmp_path / "logs"
    storage = Storage(tmp_path / "store.json")
    main.app.state.storage = storage
    scheduler = ScheduledTaskManager(storage, main.LOGS_DIR)
    scheduler.ensure_default_tasks()
    main.app.state.scheduler = scheduler
    return TestClient(main.app)


def test_task_crud(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    resp = client.post(
        "/scheduled-tasks",
        json={
            "display_name": "Daily Heartbeat",
            "function_name": "heartbeat",
            "cron": "0 9 * * *",
            "enabled": True,
            "task_id": "task-123",
        },
    )
    assert resp.status_code == 200
    task = resp.json()
    task_id = task["id"]

    resp = client.get("/scheduled-tasks")
    assert resp.status_code == 200
    assert any(item["id"] == task_id for item in resp.json()["tasks"])

    resp = client.get(f"/scheduled-tasks/{task_id}")
    assert resp.status_code == 200

    resp = client.put(
        f"/scheduled-tasks/{task_id}",
        json={
            "display_name": "Updated Heartbeat",
            "function_name": "heartbeat",
            "cron": "*/15 * * * *",
            "enabled": False,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Updated Heartbeat"

    resp = client.delete(f"/scheduled-tasks/{task_id}")
    assert resp.status_code == 200


def test_duplicate_task_id_rejected(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    payload = {
        "display_name": "Duplicate",
        "function_name": "heartbeat",
        "cron": "*/10 * * * *",
        "enabled": True,
        "task_id": "dup-1",
    }
    resp = client.post("/scheduled-tasks", json=payload)
    assert resp.status_code == 200
    resp = client.post("/scheduled-tasks", json=payload)
    assert resp.status_code == 409


def test_cron_validation_error(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    resp = client.post(
        "/scheduled-tasks",
        json={
            "display_name": "Bad Cron",
            "function_name": "heartbeat",
            "cron": "invalid",
            "enabled": True,
        },
    )
    assert resp.status_code == 400


def test_heartbeat_execution_creates_log(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "store.json")
    manager = ScheduledTaskManager(storage, tmp_path / "logs")
    manager.ensure_default_tasks()
    task = next(task for task in storage.list_scheduled_tasks() if task.function_name == "heartbeat")
    manager.start()
    execution = manager.run_task(task.id)
    manager.shutdown()

    assert execution is not None
    log_path = Path(execution.log_path)
    assert log_path.exists()
    assert "Hello Heartbeat" in log_path.read_text(encoding="utf-8")


def test_monthend_execution_creates_cobol_style_log_and_applies_interest(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "store.json")
    storage.upsert_account(
        Account(
            account_id="sav-1",
            name="Savings One",
            balance=Decimal("100.00"),
            account_type="S",
        )
    )
    storage.upsert_account(
        Account(
            account_id="chk-1",
            name="Checking One",
            balance=Decimal("100.00"),
            account_type="C",
        )
    )
    manager = ScheduledTaskManager(storage, tmp_path / "logs")
    task = create_task(
        storage,
        ScheduledTaskCreate(
            display_name="Month End Interest",
            function_name="monthend_interest",
            cron="0 0 1 * *",
            enabled=True,
            task_id="monthend-1",
        ),
    )

    manager.start()
    execution = manager.run_task(task.id)
    manager.shutdown()

    assert execution is not None
    log_path = Path(execution.log_path)
    text = log_path.read_text(encoding="utf-8")
    assert "MONTHEND INTEREST BATCH START" in text
    assert "Applying 2% annual interest to all savings accounts..." in text
    assert "Interest applied to 1 savings accounts." in text
    assert "MONTHEND INTEREST BATCH COMPLETE" in text

    savings = storage.get_account("sav-1")
    checking = storage.get_account("chk-1")
    assert savings is not None and savings.balance == Decimal("102.00")
    assert checking is not None and checking.balance == Decimal("100.00")
    transactions = storage.list_transactions(account_id="sav-1", transaction_type="I")
    assert len(transactions) == 1
    assert transactions[0].amount == Decimal("2.00")


def test_retention_prunes_old_executions(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "store.json")
    manager = ScheduledTaskManager(storage, tmp_path / "logs")
    manager.ensure_default_tasks()
    task = next(task for task in storage.list_scheduled_tasks() if task.function_name == "heartbeat")
    manager.start()
    for _ in range(55):
        manager.run_task(task.id)
    manager.shutdown()

    executions = storage.list_task_executions(task.id)
    assert len(executions) == 50
    log_files = list((tmp_path / "logs" / task.id).glob("*.log"))
    assert len(log_files) <= 50


def test_log_fetch_endpoint(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    tasks = client.get("/scheduled-tasks").json()["tasks"]
    heartbeat = next(task for task in tasks if task["function_name"] == "heartbeat")
    run_resp = client.post(f"/scheduled-tasks/{heartbeat['id']}/run")
    assert run_resp.status_code == 200
    execution_id = run_resp.json()["id"]

    log_resp = client.get(
        f"/scheduled-tasks/{heartbeat['id']}/executions/{execution_id}/log"
    )
    assert log_resp.status_code == 200
    assert "Hello Heartbeat" in log_resp.text


def test_list_log_files_endpoint(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    tasks = client.get("/scheduled-tasks").json()["tasks"]
    heartbeat = next(task for task in tasks if task["function_name"] == "heartbeat")
    run_resp = client.post(f"/scheduled-tasks/{heartbeat['id']}/run")
    assert run_resp.status_code == 200
    execution_id = run_resp.json()["id"]

    logs_resp = client.get(f"/scheduled-tasks/{heartbeat['id']}/logs")
    assert logs_resp.status_code == 200
    logs = logs_resp.json()["logs"]
    assert any(item["execution_id"] == execution_id for item in logs)


def test_monthend_task_via_api_run_and_log(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.post(
        "/accounts",
        json={
            "account_id": "sav2",
            "name": "Saver Two",
            "balance": "200.00",
            "account_type": "S",
        },
    )
    create_resp = client.post(
        "/scheduled-tasks",
        json={
            "display_name": "Month End",
            "function_name": "monthend_interest",
            "cron": "0 0 1 * *",
            "enabled": True,
            "task_id": "monthend-api",
        },
    )
    assert create_resp.status_code == 200
    task_id = create_resp.json()["id"]

    run_resp = client.post(f"/scheduled-tasks/{task_id}/run")
    assert run_resp.status_code == 200
    execution_id = run_resp.json()["id"]

    log_resp = client.get(f"/scheduled-tasks/{task_id}/executions/{execution_id}/log")
    assert log_resp.status_code == 200
    assert "MONTHEND INTEREST BATCH START" in log_resp.text
    assert "Interest applied to 1 savings accounts." in log_resp.text

    acct_resp = client.get("/accounts/sav2")
    assert acct_resp.status_code == 200
    assert acct_resp.json()["balance"] == "204.00"
