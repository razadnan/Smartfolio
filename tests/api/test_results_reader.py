import json

import pandas as pd
import pytest

from smartfolio.api.schemas import ExperimentSummary
from smartfolio.api.services import results_reader as rr


@pytest.fixture
def results(tmp_path):
    e = tmp_path / "E0"
    e.mkdir()
    m = {"annual_return": 0.1, "volatility": 0.1, "sharpe": 1.0, "sortino": 1.2,
         "calmar": 1.0, "max_drawdown": -0.1}
    (e / "summary.json").write_text(json.dumps({
        "experiment": "E0", "period": "2021-01-01/2021-01-05", "data_source": "mock",
        "synthetic": True, "net": {**m, "turnover": 0.02}, "gross": m}))
    idx = pd.bdate_range("2021-01-01", periods=3, name="date")
    pd.DataFrame({"gross": [0.01, None, 0.0], "net": [0.009, 0.0, 0.0],
                  "equity": [1.009] * 3, "drawdown": [0.0] * 3}, index=idx
                 ).to_parquet(e / "returns.parquet")
    return tmp_path


def test_summary_matches_schema(results):
    s = ExperimentSummary(**rr.experiment_summary("E0", base=results))
    assert s.synthetic is True and s.gross.turnover is None


def test_returns_are_json_safe(results):
    recs = rr.experiment_returns("E0", base=results)
    assert recs[0]["date"] == "2021-01-01"
    assert recs[1]["gross"] is None
    json.dumps(recs)


def test_missing_file_raises(results):
    with pytest.raises(rr.ResultsNotFound):
        rr.experiment_summary("E3", base=results)


def test_unknown_experiment_raises(results):
    with pytest.raises(ValueError):
        rr.experiment_summary("E9", base=results)


def test_real_results_all_validate():
    rows = rr.list_experiments()
    assert len(rows) == 7
    for r in rows:
        ExperimentSummary(**r)