import copy, json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from numpy.lib.stride_tricks import sliding_window_view
from smartfolio.forecasting.config import load_config, set_seed, ROOT
from smartfolio.forecasting.features import FEATURE_COLS
from smartfolio.forecasting.walkforward import make_folds, split
from smartfolio.forecasting.ensemble import forecast_metrics, daily_rank_ic

SEQ, HIDDEN, EPOCHS, PATIENCE, BATCH, LR = 20, 32, 20, 3, 512, 1e-3


class Net(nn.Module):
    def __init__(self, n_feat):
        super().__init__()
        self.lstm = nn.LSTM(n_feat, HIDDEN, batch_first=True)
        self.drop = nn.Dropout(0.2)
        self.fc = nn.Linear(HIDDEN, 1)

    def forward(self, x):
        o, _ = self.lstm(x)
        return self.fc(self.drop(o[:, -1])).squeeze(-1)


def build_windows(df):
    """Window for row t = features of the SEQ rows ending at t (same symbol)."""
    X, idx = [], []
    for _, g in df.groupby("symbol", sort=False):
        a = g[FEATURE_COLS].to_numpy(np.float32)
        X.append(sliding_window_view(a, SEQ, axis=0).transpose(0, 2, 1))
        idx.append(g.index[SEQ - 1:])
    return np.concatenate(X), np.concatenate(idx)


def predict(net, X):
    net.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(X), 4096):
            out.append(net(torch.from_numpy(X[i:i + 4096])).numpy())
    return np.concatenate(out)


def train(Xf, yf, Xv, yv, seed):
    net = Net(Xf.shape[2])
    opt = torch.optim.Adam(net.parameters(), lr=LR, weight_decay=1e-4)
    gen = torch.Generator().manual_seed(seed)
    Xt, yt = torch.from_numpy(Xf), torch.from_numpy(yf)
    best, best_state, bad, best_ep = np.inf, None, 0, 0
    for ep in range(EPOCHS):
        net.train()
        perm = torch.randperm(len(Xt), generator=gen)
        for i in range(0, len(perm), BATCH):
            b = perm[i:i + BATCH]
            opt.zero_grad()
            nn.functional.mse_loss(net(Xt[b]), yt[b]).backward()
            opt.step()
        v = float(np.mean((predict(net, Xv) - yv) ** 2))
        if v < best - 1e-6:
            best, bad, best_ep = v, 0, ep + 1
            best_state = copy.deepcopy(net.state_dict())
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    net.load_state_dict(best_state)
    return net, best_ep


def run():
    cfg = load_config()
    seed = cfg["seed"]
    df = (pd.read_parquet(ROOT / cfg["paths"]["features"] / "features.parquet")
            .sort_values(["symbol", "date"]).reset_index(drop=True))
    X, idx = build_windows(df)
    df = df.loc[idx].reset_index(drop=True)  # aligned row-for-row with X
    F = X.shape[2]
    out_dir = ROOT / "models/lstm"
    out_dir.mkdir(parents=True, exist_ok=True)

    oos, vals, per_fold = [], [], []
    for f in make_folds(last_year=df["date"].max().year):
        set_seed(seed)
        fit, val, test = split(df, f)
        lo, hi = fit["target"].quantile([0.01, 0.99])

        xf = X[fit.index].reshape(-1, F)              # scaler uses FIT rows only
        mu, sd = xf.mean(0), xf.std(0) + 1e-8
        sc = lambda ix: np.clip((X[ix] - mu) / sd, -5, 5).astype(np.float32)
        ysd = float(fit["target"].clip(lo, hi).std())
        yf = (fit["target"].clip(lo, hi) / ysd).to_numpy(np.float32)
        yv = (val["target"].clip(lo, hi) / ysd).to_numpy(np.float32)

        net, ep = train(sc(fit.index), yf, sc(val.index), yv, seed)

        t = test[["date", "symbol", "target", "target_date"]].copy()
        t["lstm_prediction"] = predict(net, sc(test.index)) * ysd
        t["fold"] = f["year"]
        v = val[["date", "symbol", "target"]].copy()
        v["lstm_prediction"] = predict(net, sc(val.index)) * ysd
        v["fold"] = f["year"]
        oos.append(t)
        vals.append(v)

        ev = t.dropna(subset=["target"])
        m = forecast_metrics(ev["target"], ev["lstm_prediction"])
        m.update(fold=f["year"], best_epoch=ep, rank_ic=daily_rank_ic(ev, "lstm_prediction"))
        per_fold.append(m)
        print(f"{f['year']}  epochs={ep:2d}  rmse={m['rmse']:.4f}  "
              f"dir_acc={m['directional_accuracy']:.3f}  ic={m['rank_ic']:+.3f}")

    oos = pd.concat(oos, ignore_index=True)
    vals = pd.concat(vals, ignore_index=True)
    oos.to_parquet(out_dir / "lstm_oos.parquet", index=False)
    vals.to_parquet(out_dir / "lstm_val.parquet", index=False)
    torch.save(net.state_dict(), out_dir / "lstm_latest.pt")
    np.savez(out_dir / "lstm_scaler.npz", mu=mu, sd=sd, ysd=ysd)

    ev = oos.dropna(subset=["target"])
    overall = forecast_metrics(ev["target"], ev["lstm_prediction"])
    overall["rank_ic"] = daily_rank_ic(ev, "lstm_prediction")
    with open(ROOT / cfg["paths"]["metadata"] / "lstm_metrics.json", "w") as fh:
        json.dump({"overall": overall, "per_fold": per_fold, "seq_len": SEQ,
                   "hidden": HIDDEN, "seed": seed}, fh, indent=2)
    print("OVERALL:", {k: round(v, 4) for k, v in overall.items()})


if __name__ == "__main__":
    run()