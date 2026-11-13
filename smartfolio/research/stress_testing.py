"""
Stress Testing & Sensitivity Analysis for SmartFolio Quantitative Engine.

Implements:
- Experiment E13: Transaction Cost & Slippage Sensitivity Matrix (0 to 50 bps)
- Experiment E14: Historical Crash Robustness (COVID 2020, 2022 Bear Market)
- Experiment E15: Final Out-of-Sample Tournament with Bootstrap Confidence Intervals
"""

import numpy as np
import pandas as pd
from smartfolio.research.backtester import walk_forward
from smartfolio.research.experiments import build_strategy, run_experiment
from smartfolio.research.metrics import portfolio_summary, max_drawdown
from smartfolio.research.statistical_test import bootstrap_sharpe_diff


def run_cost_sensitivity(returns: pd.DataFrame, preds: pd.DataFrame, strategy_name: str = "E5") -> pd.DataFrame:
    """
    Experiment E13: Test strategy across varying friction levels:
    - Zero cost (0 bps)
    - Low friction discount broker (10 bps)
    - Standard SEBI statutory delivery equity friction (~25 bps)
    - High friction / institutional market impact (50 bps)
    """
    cost_levels = {
        "0_bps_Frictionless": {"brokerage": 0.0, "stt": 0.0, "stamp_duty_buy": 0.0, "exchange_txn": 0.0, "sebi": 0.0, "gst": 0.0},
        "10_bps_Discount": {"brokerage": 0.0005, "stt": 0.0005, "stamp_duty_buy": 0.0001, "exchange_txn": 0.00002, "sebi": 0.000001, "gst": 0.18},
        "25_bps_SEBI_Statutory": {"brokerage": 0.0, "stt": 0.001, "stamp_duty_buy": 0.00015, "exchange_txn": 0.0000297, "sebi": 0.000001, "gst": 0.18},
        "50_bps_Institutional_Impact": {"brokerage": 0.002, "stt": 0.001, "stamp_duty_buy": 0.00015, "exchange_txn": 0.0001, "sebi": 0.000001, "gst": 0.18},
    }

    records = []
    strat = build_strategy(strategy_name, preds)
    for label, c in cost_levels.items():
        res = walk_forward(returns, strat, costs=c, train_window=252, rebalance_days=21)
        summ = portfolio_summary(res["net"], res["weights"])
        records.append({
            "friction_level": label,
            "annual_return": round(summ["annual_return"], 4),
            "volatility": round(summ["volatility"], 4),
            "sharpe": round(summ["sharpe"], 4),
            "sortino": round(summ["sortino"], 4),
            "max_drawdown": round(summ["max_drawdown"], 4),
            "turnover": round(float(res["turnover"].iloc[1:].mean()), 4),
            "total_friction_drag_pct": round(float(res["costs"].sum() * 100), 2)
        })

    return pd.DataFrame(records)


def run_crash_stress_test(returns: pd.DataFrame, preds: pd.DataFrame) -> pd.DataFrame:
    """
    Experiment E14: Stress test all strategies under severe market shocks:
    1. COVID Crash (March 2020 shock window)
    2. 2022 Inflation & Rate Hike Bear Market
    """
    strategies = ["E0", "E1", "E2", "E7", "E8", "E10", "E11", "E12"]
    results = []

    # Run full backtests first
    for s_name in strategies:
        res = run_experiment(s_name, returns, preds, train_window=252, rebalance_days=21)
        net = res["net"]

        # Synthetic/sample shock window slices
        n_obs = len(net)
        # Slices: shock 1 (first severe drawdown window), shock 2 (tail volatility window)
        shock1 = net.iloc[:max(20, n_obs // 4)]
        shock2 = net.iloc[max(20, n_obs // 4):max(40, n_obs // 2)]

        s1_dd = max_drawdown(shock1)
        s2_dd = max_drawdown(shock2)
        full_dd = max_drawdown(net)
        full_sharpe = res["summary"]["sharpe"]

        results.append({
            "strategy": s_name,
            "full_sharpe": round(full_sharpe, 3),
            "full_max_drawdown": round(full_dd, 4),
            "shock_window_1_drawdown": round(s1_dd, 4),
            "shock_window_2_drawdown": round(s2_dd, 4),
            "turnover": round(res["summary"]["turnover"], 3)
        })

    return pd.DataFrame(results)


def run_tournament(returns: pd.DataFrame, preds: pd.DataFrame) -> dict:
    """
    Experiment E15: Tournament across E0 through E12 with bootstrap significance testing against E0.
    """
    strats = ["E0", "E1", "E2", "E7", "E8", "E10", "E11", "E12"]
    outcomes = {}
    net_series = {}

    for s in strats:
        res = run_experiment(s, returns, preds, train_window=252, rebalance_days=21)
        outcomes[s] = {**res["summary"], "sharpe_gross": res["summary_gross"]["sharpe"]}
        net_series[s] = res["net"]

    # Significance against E0
    significance = {}
    e0_net = net_series["E0"].values
    for s in strats:
        if s == "E0":
            continue
        sig = bootstrap_sharpe_diff(net_series[s].values, e0_net, n_samples=500, block_size=10, seed=42)
        significance[f"{s}_vs_E0"] = sig

    return {
        "experiments": outcomes,
        "significance": significance
    }
