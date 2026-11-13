from fastapi.testclient import TestClient

from smartfolio.api.main import app
from smartfolio.api.services import results_reader as rr

client = TestClient(app)


def test_list_experiments():
    r = client.get("/experiments")
    assert r.status_code == 200
    assert [e["experiment"] for e in r.json()] == ["E0", "E1", "E2", "E3", "E4", "E5", "E6"]


def test_single_experiment_and_invalid_name():
    assert client.get("/experiments/E6").json()["experiment"] == "E6"
    assert client.get("/experiments/E9").status_code == 422


def test_model_comparison():
    body = client.get("/model-comparison").json()
    assert len(body["experiments"]) == 7
    assert {"E6_vs_E0", "E6_vs_E2"} <= set(body["significance"])
    assert "synthetic" in body


def test_backtest_and_weights():
    b = client.get("/backtest?experiment=E5").json()
    assert b["summary"]["experiment"] == "E5"
    assert {"date", "net", "equity", "drawdown"} <= set(b["returns"][0])
    w = client.get("/backtest/weights?experiment=E0").json()
    assert w["weights"][0]["decision_date"]


def test_missing_results_gives_clean_404(monkeypatch, tmp_path):
    monkeypatch.setattr(rr, "RESULTS_DIR", tmp_path)
    r = client.get("/model-comparison")
    assert r.status_code == 404
    assert r.json()["error"] == "results_not_found"
    assert client.get("/experiments").json() == []


def test_extended_experiments_endpoints():
    r1 = client.get("/extended-comparison")
    assert r1.status_code == 200
    assert len(r1.json()["experiments"]) >= 12

    r2 = client.get("/cost-sensitivity")
    assert r2.status_code == 200
    assert len(r2.json()) == 4

    r3 = client.get("/stress-tests")
    assert r3.status_code == 200
    assert len(r3.json()) >= 8

    r4 = client.get("/tournament")
    assert r4.status_code == 200
    assert "E0" in r4.json()["experiments"]
