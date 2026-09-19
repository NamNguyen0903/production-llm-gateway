from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.dependencies import auth
from app.db.models.api_key import ApiKey

TEST_KEY = "gw_" + "a" * 64
TEST_SECRET = "b" * 64


@pytest.fixture(autouse=True)
def use_test_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(
        api_key_hmac_secret=SecretStr(TEST_SECRET),
    )
    monkeypatch.setattr(auth, "get_settings", lambda: settings)


def make_record(
    *,
    status: str = "active",
    expires_at: datetime | None = None,
) -> ApiKey:
    return ApiKey(
        id=uuid4(),
        name="test-client",
        status=status,
        rate_limit_rpm=30,
        expires_at=expires_at,
    )


def test_valid_key_returns_identity(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = make_record()
    lookup = AsyncMock(return_value=record)
    monkeypatch.setattr(auth.ApiKeyRepository, "get_by_digest", lookup)

    response = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "api_key_id": str(record.id),
        "name": "test-client",
    }
    assert "key_digest" not in response.text
    assert TEST_KEY not in response.text
    lookup.assert_awaited_once()


@pytest.mark.parametrize("case", ["unknown", "revoked", "expired"])
def test_unusable_key_returns_401(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    record = None

    if case == "revoked":
        record = make_record(status="revoked")
    elif case == "expired":
        record = make_record(
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )

    lookup = AsyncMock(return_value=record)
    monkeypatch.setattr(auth.ApiKeyRepository, "get_by_digest", lookup)

    response = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "INVALID_API_KEY"


@pytest.mark.parametrize(
    "failure",
    [
        ConnectionRefusedError("test database unavailable"),
        TimeoutError("test database timeout"),
    ],
)
def test_database_failure_returns_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
) -> None:
    lookup = AsyncMock(side_effect=failure)
    monkeypatch.setattr(auth.ApiKeyRepository, "get_by_digest", lookup)

    response = client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
    )

    assert response.status_code == 503

    error = response.json()["error"]

    assert error["code"] == "AUTHENTICATION_UNAVAILABLE"
    assert error["retryable"] is True
    assert error["request_id"] == response.headers["x-request-id"]
    assert str(failure) not in response.text


def test_malformed_key_does_not_query_database(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lookup = AsyncMock()
    monkeypatch.setattr(auth.ApiKeyRepository, "get_by_digest", lookup)

    response = client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer invalid"},
    )

    assert response.status_code == 401
    lookup.assert_not_awaited()
