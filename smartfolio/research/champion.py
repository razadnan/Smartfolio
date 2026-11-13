import pandas as pd

from smartfolio.research.backtester import walk_forward
from smartfolio.research.challenger import evaluate_challenger
from smartfolio.research.config import load_config
from smartfolio.research.experiments import model_strategy
from smartfolio.research.feedback import FeedbackTracker, portfolio_feedback, prediction_feedback
from smartfolio.research.metrics import portfolio_summary


def run_e6(returns, train_fn, eval_window=None, **kw):
    """E6: ensemble-style forecasting + optimizer + feedback + gated retraining.
    train_fn(train_returns, version) -> model with .version and .predict(history, date)."""
    ev = eval_window or load_config()["retraining"]["eval_window_days"]
    tracker = FeedbackTracker()
    state = {"champ": None, "cutoff": None, "last": None, "n": 1}
    pred_rows, decisions = [], []

    def strat(h, d):
        end = len(h)
        if state["champ"] is None:
            state.update(champ=train_fn(h, "v1"), cutoff=end, last=end)
        else:
            for j in range(state["last"], end):          # log champion's daily forecasts
                p = state["champ"].predict(h.iloc[:j + 1], h.index[j])
                pred_rows.extend({"date": h.index[j], "symbol": s, "prediction": v}
                                 for s, v in p.items())
            state["last"] = end
            fb = prediction_feedback(pd.DataFrame(pred_rows), h, "prediction")
            chk = tracker.check(fb, d, h.index)
            if chk["retrain"]:
                start = end - ev
                if start <= state["cutoff"]:
                    if not decisions or decisions[-1]["decision"] != "SKIPPED":
                        decisions.append({"date": str(d.date()), "decision": "SKIPPED",
                                          "reason": "evaluation window overlaps champion training data"})
                else:
                    chal = train_fn(h.iloc[:start], f"v{state['n'] + 1}")
                    rec = evaluate_challenger(state["champ"], chal, h, start, end,
                                              kw.get("rebalance_days"))
                    rec.update(date=str(d.date()), feedback_trigger=chk,
                               champion_train_end=str(h.index[state["cutoff"] - 1].date()),
                               challenger_train_end=str(h.index[start - 1].date()))
                    decisions.append(rec)
                    tracker.mark_retrained(d)
                    state["n"] += 1
                    if rec["decision"] == "PROMOTED":
                        state.update(champ=chal, cutoff=start)
        return model_strategy(state["champ"])(h, d)

    res = walk_forward(returns, strat, **kw)
    res["turnover"] = res["turnover"]  # already returned by walk_forward
    res.update(experiment="E6", decisions=decisions, champion_final=state["champ"].version,
               summary=portfolio_summary(res["net"], res["weights"]),
               summary_gross=portfolio_summary(res["gross"]),
               portfolio_feedback=portfolio_feedback(res["weights"], res["net"]),
               prediction_feedback=(prediction_feedback(pd.DataFrame(pred_rows), returns, "prediction")
                                    if pred_rows else pd.DataFrame()))
    res["summary"]["turnover"] = float(res["turnover"].iloc[1:].mean())
    return res