import numpy as np

from smartfolio.research import metrics as m
from smartfolio.research.backtester import walk_forward
from smartfolio.research.config import load_config
from smartfolio.research.experiments import model_strategy
from smartfolio.research.feedback import forward_returns
from smartfolio.research.statistical_test import promotion_decision


def prediction_metrics(model, returns, start, end, horizon=None):
    """Forecast accuracy on decision days whose outcomes are known before `end`."""
    h = horizon or load_config()["forecast_horizon_days"]
    fwd = forward_returns(returns.iloc[:end], h)
    ys, ps = [], []
    for j in range(start - 1, end - h):
        p = model.predict(returns.iloc[:j + 1], returns.index[j])
        ys.append(fwd.iloc[j].reindex(p.index).values)
        ps.append(p.values)
    y, p = np.concatenate(ys), np.concatenate(ps)
    return {"mae": m.mae(y, p), "rmse": m.rmse(y, p), "r2": m.r2(y, p),
            "directional_accuracy": m.directional_accuracy(y, p)}


def eval_returns(model, returns, start, end, rebalance_days=None):
    """Net returns of the model's portfolio on positions [start, end)."""
    res = walk_forward(returns.iloc[:end], model_strategy(model),
                       train_window=start, rebalance_days=rebalance_days)
    return res["net"]


def evaluate_challenger(champion, challenger, returns, start, end, rebalance_days=None):
    """Both models on the SAME unseen window [start, end). Decision = bootstrap gate."""
    r_champ = eval_returns(champion, returns, start, end, rebalance_days)
    r_chal = eval_returns(challenger, returns, start, end, rebalance_days)
    pm_champ = prediction_metrics(champion, returns, start, end)
    pm_chal = prediction_metrics(challenger, returns, start, end)
    dec = promotion_decision(r_chal.values, r_champ.values)
    return {
        "champion_version": champion.version,
        "challenger_version": challenger.version,
        "evaluation_period": f"{returns.index[start].date()}/{returns.index[end - 1].date()}",
        "prediction_metrics": {"champion": pm_champ, "challenger": pm_chal},
        "accuracy_improved": pm_chal["rmse"] < pm_champ["rmse"],
        "sharpe_champion": m.sharpe(r_champ),
        "sharpe_challenger": m.sharpe(r_chal),
        **dec,
    }