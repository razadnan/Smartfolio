from fastapi.testclient import TestClient

from smartfolio.api.main import app
from smartfolio.api.services import results_reader as rr
from smartfolio.api.services.promotions import summarize

client = TestClient(app)

DECS = [
    {"date": "a", "decision": "SKIPPED"},
    {"date": "b", "decision": "REJECTED", "champion_version": "v1",
     "challenger_version": "v2", "accuracy_improved": True},
    {"date": "c", "decision": "PROMOTED", "champion_version": "v1",
     "challenger_version": "v3", "accuracy_improved": False},
    {"date": "d", "decision": "REJECTED", "champion_version": "v3",
     "challenger_version": "v4", "accuracy_improved": False},
]


def test_summarize_counts():
    s = summarize(DECS)
    assert s["counts"] == {"PROMOTED": 1, "REJECTED": 2, "SKIPPED": 1}
    assert s["current_champion"] == "v3"
    assert s["accuracy_improved_but_rejected"] == 1


def test_summarize_empty():
    s = summarize([])
    assert s["current_champion"] is None and s["counts"]["REJECTED"] == 0


def test_champion_challenger_endpoint():
    body = client.get("/champion-challenger").json()
    assert sum(body["counts"].values()) == len(body["decisions"]) > 0
    assert all("decision" in d and "date" in d for d in body["decisions"])


def test_feedback_overview():
    body = client.get("/feedback").json()
    assert body["prediction_total"] > 0
    assert len(body["portfolio"]) == body["portfolio_periods"] > 0


def test_prediction_feedback_pagination():
    body = client.get("/feedback/prediction?limit=5&offset=2").json()
    assert len(body["rows"]) == 5 and body["total"] > 5 and body["offset"] == 2
    assert {"date", "symbol", "prediction", "actual", "known_by"} <= set(body["rows"][0])


def test_pagination_limits_validated():
    assert client.get("/feedback/prediction?limit=0").status_code == 422
    assert client.get("/feedback/prediction?limit=9999").status_code == 422


def test_missing_results_404(monkeypatch, tmp_path):
    monkeypatch.setattr(rr, "RESULTS_DIR", tmp_path)
    assert client.get("/champion-challenger").status_code == 404
    assert client.get("/feedback").status_code == 404