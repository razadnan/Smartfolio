import json
import pandas as pd
import xgboost as xgb
from smartfolio.forecasting.config import load_config, set_seed, ROOT
from smartfolio.forecasting.features import FEATURE_COLS
from smartfolio.forecasting.walkforward import make_folds, split
from smartfolio.forecasting.ensemble import forecast_metrics, daily_rank_ic

PARAMS = dict(n_estimators=500, learning_rate=0.03, max_depth=4, min_child_weight=50,
              subsample=0.8, colsample_bytree=0.8, reg_lambda=5.0,
              early_stopping_rounds=30, tree_method="hist", n_jobs=-1)


def run():
    cfg = load_config()
    seed = cfg["seed"]
    set_seed(seed)
    df = pd.read_parquet(ROOT / cfg["paths"]["features"] / "features.parquet")
    out_dir = ROOT / "models/xgboost"
    out_dir.mkdir(parents=True, exist_ok=True)

    oos, vals, per_fold = [], [], []
    for f in make_folds(last_year=df["date"].max().year):
        fit, val, test = split(df, f)
        lo, hi = fit["target"].quantile([0.01, 0.99])
        model = xgb.XGBRegressor(**PARAMS, random_state=seed)
        model.fit(fit[FEATURE_COLS], fit["target"].clip(lo, hi),
                  eval_set=[(val[FEATURE_COLS], val["target"].clip(lo, hi))],
                  verbose=False)

        t = test[["date", "symbol", "target", "target_date"]].copy()
        t["xgb_prediction"] = model.predict(test[FEATURE_COLS])
        t["fold"] = f["year"]
        v = val[["date", "symbol", "target"]].copy()
        v["xgb_prediction"] = model.predict(val[FEATURE_COLS])
        v["fold"] = f["year"]
        oos.append(t)
        vals.append(v)

        ev = t.dropna(subset=["target"])
        m = forecast_metrics(ev["target"], ev["xgb_prediction"])
        m.update(fold=f["year"], best_iter=int(model.best_iteration),
                 rank_ic=daily_rank_ic(ev, "xgb_prediction"))
        per_fold.append(m)
        print(f"{f['year']}  iters={m['best_iter']:3d}  rmse={m['rmse']:.4f}  "
              f"dir_acc={m['directional_accuracy']:.3f}  ic={m['rank_ic']:+.3f}")

    oos = pd.concat(oos, ignore_index=True)
    vals = pd.concat(vals, ignore_index=True)
    oos.to_parquet(out_dir / "xgb_oos.parquet", index=False)
    vals.to_parquet(out_dir / "xgb_val.parquet", index=False)
    model.save_model(out_dir / "xgb_latest.json")

    ev = oos.dropna(subset=["target"])
    overall = forecast_metrics(ev["target"], ev["xgb_prediction"])
    overall["rank_ic"] = daily_rank_ic(ev, "xgb_prediction")
    meta = ROOT / cfg["paths"]["metadata"]
    with open(meta / "xgb_metrics.json", "w") as fh:
        json.dump({"overall": overall, "per_fold": per_fold,
                   "params": PARAMS, "seed": seed}, fh, indent=2)
    print("OVERALL:", {k: round(v, 4) for k, v in overall.items()})


if __name__ == "__main__":
    run()