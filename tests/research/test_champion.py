from smartfolio.research.challenger import evaluate_challenger, prediction_metrics
from smartfolio.research.champion import run_e6
from smartfolio.research.mock_data import make_returns
from smartfolio.research.stand_ins import MomentumModel, train_momentum


def test_prediction_metrics_keys():
    R = make_returns(400)
    pm = prediction_metrics(MomentumModel(20, "x"), R, 300, 400)
    assert set(pm) == {"mae", "rmse", "r2", "directional_accuracy"}


def test_required_rejection_case():
    """Better forecast accuracy, but no significant portfolio-level gain -> REJECTED."""
    R = make_returns(600)
    champ = MomentumModel(20, "champion")
    chal = MomentumModel(20, "challenger", scale=0.5, noise=0.005)
    rec = evaluate_challenger(champ, chal, R, 300, 400, rebalance_days=21)
    assert rec["accuracy_improved"]
    assert rec["decision"] == "REJECTED"
    assert rec["confidence_interval"][0] <= 0


def test_e6_runs_and_logs_decisions():
    R = make_returns(700)
    res = run_e6(R, train_momentum, train_window=200, rebalance_days=21, eval_window=63)
    assert len(res["net"]) == 500
    real = [d for d in res["decisions"] if d["decision"] != "SKIPPED"]
    assert len(real) >= 1
    for d in real:
        start = d["evaluation_period"].split("/")[0]
        assert d["decision"] in ("PROMOTED", "REJECTED")
        assert d["challenger_train_end"] < start      # challenger never saw eval data
        assert d["champion_train_end"] < start
        assert d["seed"] == 42 and len(d["confidence_interval"]) == 2