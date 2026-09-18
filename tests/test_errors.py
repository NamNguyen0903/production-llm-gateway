from fastapi.testclient import TestClient


def test_not_found_uses_standard_error_response(
    client: TestClient,
) -> None:
    response = client.get("/not-found")

    assert response.status_code == 404

    body = response.json()
    error = body["error"]

    assert error["code"] == "NOT_FOUND"
    assert error["message"] == "The requested resource was not found."
    assert error["retryable"] is False
    assert error["details"] is None
    assert error["request_id"] == response.headers["x-request-id"]


def test_method_not_allowed_uses_standard_error_response(
    client: TestClient,
) -> None:
    response = client.post("/health/live")

    assert response.status_code == 405
    assert response.headers["allow"] == "GET"

    body = response.json()
    error = body["error"]

    assert error["code"] == "METHOD_NOT_ALLOWED"
    assert error["retryable"] is False
    assert error["request_id"] == response.headers["x-request-id"]


def test_each_request_receives_a_different_request_id(
    client: TestClient,
) -> None:
    first_response = client.get("/health/live")
    second_response = client.get("/health/live")

    first_request_id = first_response.headers["x-request-id"]
    second_request_id = second_response.headers["x-request-id"]

    assert first_request_id != second_request_id