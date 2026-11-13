import json
import numpy as np
import pandas as pd
from smartfolio.forecasting.config import load_config, ROOT

def forecast_metrics(y, p):
    y, p = np.asarray(y), np.asarray(p)
    err = y - p
    return {
        "mae": float(np.abs(err).mean()),
        "rmse": float(np.sqrt((err ** 2).mean())),
        "r2": float(1 - (err ** 2).sum() / ((y - y.mean()) ** 2).sum()),
        "directional_accuracy": float((np.sign(y) == np.sign(p)).mean()),
        "base_rate_up": float((y > 0).mean()),
        "n": int(len(y)),
    }

def daily_rank_ic(df, pred_col):
    ic = df.groupby("date")[[pred_col, "target"]].apply(
        lambda g: g[pred_col].corr(g["target"], method="spearman")
    )
    return float(ic.mean())

REQUIRED = ["date", "symbol", "xgb_prediction", "lstm_prediction",
            "ensemble_prediction", "model_version"]
KEYS = ["date", "symbol"]


def inv_mse_weights(val, xcol="xgb_prediction", lcol="lstm_prediction"):
    v = val.dropna(subset=["target", xcol, lcol])
    ix = 1.0 / np.mean((v["target"] - v[xcol]) ** 2)
    il = 1.0 / np.mean((v["target"] - v[lcol]) ** 2)
    return float(ix / (ix + il)), float(il / (ix + il))


def combine(x, l, w_x):
    """Weighted average; if one model is missing, use the other."""
    both = w_x * x + (1 - w_x) * l
    return both.where(x.notna() & l.notna(), x.fillna(l))


def run():
    cfg = load_config()
    xo = pd.read_parquet(ROOT / "models/xgboost/xgb_oos.parquet")
    lo = pd.read_parquet(ROOT / "models/lstm/lstm_oos.parquet")
    xv = pd.read_parquet(ROOT / "models/xgboost/xgb_val.parquet")
    lv = pd.read_parquet(ROOT / "models/lstm/lstm_val.parquet")

    val = xv.merge(lv[KEYS + ["lstm_prediction"]], on=KEYS, how="inner")
    w = {int(f): inv_mse_weights(g)[0] for f, g in val.groupby("fold")}

    oos = xo.merge(lo[KEYS + ["lstm_prediction"]], on=KEYS, how="left")
    oos["w_xgb"] = oos["fold"].map(w)
    oos["ensemble_prediction"] = combine(oos["xgb_prediction"], oos["lstm_prediction"], oos["w_xgb"])
    oos["model_version"] = cfg["model"]["model_version"]
    oos["prediction_horizon"] = cfg["model"]["horizon_days"]
    oos["feature_version"] = cfg["model"]["feature_version"]

    cols = REQUIRED + ["prediction_horizon", "feature_version", "fold", "w_xgb"]
    out = oos[cols].sort_values(KEYS).reset_index(drop=True)
    assert not out["ensemble_prediction"].isna().any(), "NaN ensemble predictions"
    assert not out.duplicated(KEYS).any(), "duplicate (date, symbol)"
    out.to_parquet(ROOT / cfg["paths"]["processed"] / "prediction.parquet", index=False)

    (ROOT / "examples").mkdir(exist_ok=True)
    recent = out[out["date"] >= out["date"].max() - pd.Timedelta(days=10)]
    recent.to_csv(ROOT / "examples/prediction_sample.csv", index=False)

    ev = oos.dropna(subset=["target", "xgb_prediction", "lstm_prediction"])
    res = {}
    for name in ["xgb_prediction", "lstm_prediction", "ensemble_prediction"]:
        m = forecast_metrics(ev["target"], ev[name])
        m["rank_ic"] = daily_rank_ic(ev, name)
        res[name] = m
        print(f"{name:20s} rmse={m['rmse']:.4f} r2={m['r2']:+.4f} "
              f"dir_acc={m['directional_accuracy']:.3f} ic={m['rank_ic']:+.4f}")
    print("weights xgb by fold:", {k: round(v, 2) for k, v in w.items()})
    print("rows:", len(out), "| latest date:", out["date"].max().date())

    with open(ROOT / cfg["paths"]["metadata"] / "ensemble_metrics.json", "w") as fh:
        json.dump({"metrics": res, "xgb_weights_by_fold": w}, fh, indent=2)


if __name__ == "__main__":
    run()