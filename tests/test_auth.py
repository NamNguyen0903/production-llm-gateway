import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Basic invalid"},
        {"Authorization": "Bearer"},
    ],
)
def test_missing_or_wrong_authentication_is_rejected(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    response = client.get("/v1/auth/me", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"

    error = response.json()["error"]

    assert error["code"] == "INVALID_API_KEY"
    assert error["retryable"] is False
    assert error["request_id"] == response.headers["x-request-id"]


def test_liveness_remains_public(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
