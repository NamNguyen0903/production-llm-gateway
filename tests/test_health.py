from fastapi.testclient import TestClient


def test_liveness_returns_alive(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_liveness_returns_internal_request_id(client: TestClient) -> None:
    response = client.get("/health/live")

    request_id = response.headers["x-request-id"]

    assert request_id.startswith("req_")
    assert len(request_id) > len("req_")