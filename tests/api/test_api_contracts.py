import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["app_name"] == "AI Engineering Copilot"
    assert payload["app_env"] in {"development", "testing", "production"}
    assert isinstance(payload["app_version"], str)
    assert payload["app_version"]


@pytest.mark.parametrize(
    ("path", "module_name"),
    [
        ("/api/v1/chat/status", "chat"),
        ("/api/v1/review/status", "review"),
        ("/api/v1/planner/status", "planner"),
        ("/api/v1/documentation/status", "documentation"),
        ("/api/v1/evaluation/status", "evaluation"),
    ],
)
def test_module_status_endpoints(
    path: str,
    module_name: str,
) -> None:
    response = client.get(path)

    assert response.status_code == 200

    payload = response.json()

    assert payload["module"] == module_name
    assert payload["status"] == "ready"
