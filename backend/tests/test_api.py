from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_uses_success_envelope() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["status"] == "ok"


def test_openapi_contains_versioned_core_routes() -> None:
    schema = app.openapi()
    paths = schema["paths"]
    assert "/api/v1/students" in paths
    assert "/api/v1/attendance/bulk" in paths
    assert "/api/v1/health/ready" in paths
    assert "/api/v1/auth/status" in paths
    assert "/api/v1/auth/bootstrap-super-admin" in paths
    assert "/api/v1/registration/admin" in paths
    assert "/api/v1/registration/requests/{request_id}/approve" in paths


def test_unknown_route_uses_standard_error_envelope() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/not-a-route")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
