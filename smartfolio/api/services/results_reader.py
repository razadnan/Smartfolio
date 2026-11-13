"""
results_reader.py — Adapter over Student 3's results/ directory.
All API endpoints read from here. No research math lives in this file.
"""
import json
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException

RESULTS_DIR = Path(__file__).resolve().parents[3] / "results"
EXPERIMENTS = ["E0", "E1", "E2", "E3", "E4", "E5", "E6"]


class ResultsNotFound(Exception):
    pass


VALID_EXPERIMENTS = {"E0", "E1", "E2", "E3", "E4", "E5", "E6"}

def _summary_path(name: str, base: Path = None) -> Path:
    if name not in VALID_EXPERIMENTS:
        raise ValueError(f"Unknown experiment: {name!r}. Valid: {sorted(VALID_EXPERIMENTS)}")
    d = (base or RESULTS_DIR) / name / "summary.json"
    if not d.exists():
        raise ResultsNotFound(f"No results for {name}")
    return d


# ── experiment helpers ────────────────────────────────────────────────────────

def experiment_summary(name: str, base: Path = None) -> dict:
    return json.loads(_summary_path(name, base).read_text())


def list_experiments(base: Path = None) -> list[dict]:
    out = []
    for name in EXPERIMENTS:
        try:
            out.append(experiment_summary(name, base))
        except ResultsNotFound:
            pass
    return out


def experiment_returns(name: str, base: Path = None) -> list[dict]:
    p = (base or RESULTS_DIR) / name / "returns.parquet"
    if not p.exists():
        raise ResultsNotFound(f"No returns for {name}")
    df = pd.read_parquet(p).reset_index()
    df.columns = [str(c) for c in df.columns]
    # Rename index column to 'date' if present
    if "date" not in df.columns and df.columns[0] != "date":
        df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    # Replace NaN with None for JSON safety
    return [
        {k: (None if pd.isna(v) else v) for k, v in row.items()}
        for row in df.to_dict(orient="records")
    ]


def experiment_weights(name: str, base: Path = None) -> list[dict]:
    p = (base or RESULTS_DIR) / name / "weights.parquet"
    if not p.exists():
        raise ResultsNotFound(f"No weights for {name}")
    df = pd.read_parquet(p)
    records = []
    for decision_date, row in df.iterrows():
        for symbol, weight in row.items():
            if weight > 0:
                records.append({
                    "decision_date": str(decision_date)[:10],
                    "symbol": symbol,
                    "weight": round(float(weight), 6),
                })
    return records


def comparison(base: Path = None) -> dict:
    p = (base or RESULTS_DIR) / "comparison.json"
    if not p.exists():
        raise ResultsNotFound(f"comparison.json not found in {base or RESULTS_DIR}")
    data = json.loads(p.read_text())
    # Add significance placeholder if not present
    if "significance" not in data:
        data["significance"] = {"E6_vs_E0": None, "E6_vs_E2": None}
    return data


def promotions(base: Path = None) -> list[dict]:
    p = (base or RESULTS_DIR) / "model_promotions.json"
    if not p.exists():
        raise ResultsNotFound("model_promotions.json not found")
    return json.loads(p.read_text())


def feedback(kind: str, base: Path = None) -> list[dict]:
    """kind = 'prediction' | 'portfolio'"""
    root = base or RESULTS_DIR
    if not root.exists():
        raise ResultsNotFound(f"Results directory not found: {root}")

    # Check parquet first
    target_parquet = "prediction_feedback.parquet" if kind == "prediction" else "portfolio_feedback.parquet"
    for name in ["E6", "E5", "E4", "E3", "E2", "E1", "E0"]:
        p = root / name / target_parquet
        if p.exists():
            df = pd.read_parquet(p).reset_index()
            for col in df.columns:
                if "date" in str(col).lower() or "period" in str(col).lower() or "known_by" in str(col).lower():
                    df[col] = df[col].astype(str).str[:10]
            records = [
                {k: (None if pd.isna(v) else v) for k, v in row.items()}
                for row in df.to_dict(orient="records")
            ]
            if records:
                return records

    # Fallback to decisions.json
    for name in ["E6", "E5", "E4", "E3", "E2", "E1", "E0"]:
        p = root / name / "decisions.json"
        if p.exists():
            data = json.loads(p.read_text())
            if kind == "portfolio":
                return data
            rows = []
            for d in data:
                if "symbol" in d:
                    rows.append({
                        "date": str(d.get("date", ""))[:10],
                        "symbol": d.get("symbol", ""),
                        "prediction": d.get("prediction"),
                        "actual": d.get("actual"),
                        "known_by": str(d.get("known_by", ""))[:10],
                    })
            if rows:
                return rows

    raise ResultsNotFound("No feedback data found in results directory")


def comparison_extended(base: Path = None) -> dict:
    p = (base or RESULTS_DIR) / "comparison_extended.json"
    if not p.exists():
        raise ResultsNotFound("comparison_extended.json not found")
    return json.loads(p.read_text())


def cost_sensitivity(base: Path = None) -> list[dict]:
    p = (base or RESULTS_DIR) / "cost_sensitivity.json"
    if not p.exists():
        raise ResultsNotFound("cost_sensitivity.json not found")
    return json.loads(p.read_text())


def stress_tests(base: Path = None) -> list[dict]:
    p = (base or RESULTS_DIR) / "stress_tests.json"
    if not p.exists():
        raise ResultsNotFound("stress_tests.json not found")
    return json.loads(p.read_text())


def tournament_results(base: Path = None) -> dict:
    p = (base or RESULTS_DIR) / "tournament_results.json"
    if not p.exists():
        raise ResultsNotFound("tournament_results.json not found")
    return json.loads(p.read_text())
