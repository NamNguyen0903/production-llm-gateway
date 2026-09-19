from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from pytest import MonkeyPatch


def test_liveness_returns_alive(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_liveness_returns_internal_request_id(client: TestClient) -> None:
    response = client.get("/health/live")

    request_id = response.headers["x-request-id"]

    assert request_id.startswith("req_")
    assert len(request_id) > len("req_")


def test_readiness_returns_ready(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    database_check = AsyncMock()

    monkeypatch.setattr(
        "app.api.routes.health.check_database_connection",
        database_check,
    )

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    database_check.assert_awaited_once_with()


def test_readiness_returns_service_unavailable_when_database_fails(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    database_check = AsyncMock(
        side_effect=RuntimeError("database unavailable"),
    )

    monkeypatch.setattr(
        "app.api.routes.health.check_database_connection",
        database_check,
    )

    response = client.get("/health/ready")

    assert response.status_code == 503

    error = response.json()["error"]

    assert error["code"] == "DATABASE_UNAVAILABLE"
    assert error["message"] == "Database is unavailable."
    assert error["retryable"] is True
    assert error["request_id"] == response.headers["x-request-id"]

    database_check.assert_awaited_once_with()


def test_liveness_does_not_check_database(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    database_check = AsyncMock(
        side_effect=RuntimeError("database unavailable"),
    )

    monkeypatch.setattr(
        "app.api.routes.health.check_database_connection",
        database_check,
    )

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}

    database_check.assert_not_awaited()
