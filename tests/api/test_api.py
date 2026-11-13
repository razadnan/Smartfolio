from fastapi.testclient import TestClient

from smartfolio.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["results_available"] is True   # needs Student 3's run_all.py output