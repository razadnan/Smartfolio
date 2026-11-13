from typing import Literal
from fastapi import APIRouter, HTTPException
from smartfolio.api.schemas import ExperimentSummary
from smartfolio.api.services import results_reader as rr

router = APIRouter(tags=["experiments"])
Experiment = Literal["E0", "E1", "E2", "E3", "E4", "E5", "E6"]


@router.get("/experiments", response_model=list[ExperimentSummary])
def list_experiments():
    return rr.list_experiments()


@router.get("/experiments/{name}", response_model=ExperimentSummary)
def get_experiment(name: Experiment):
    try:
        return rr.experiment_summary(name)
    except rr.ResultsNotFound:
        raise HTTPException(status_code=404, detail={"error": "results_not_found"})


@router.get("/model-comparison")
def model_comparison():
    """E0-E6 metrics plus bootstrap significance."""
    try:
        return rr.comparison()
    except rr.ResultsNotFound as e:
        raise HTTPException(status_code=404, detail={"error": "results_not_found", "message": str(e)})


@router.get("/extended-comparison")
def extended_comparison():
    """E0-E12 metrics across all tested models and optimizers."""
    try:
        return rr.comparison_extended()
    except rr.ResultsNotFound as e:
        raise HTTPException(status_code=404, detail={"error": "results_not_found", "message": str(e)})


@router.get("/cost-sensitivity")
def cost_sensitivity():
    """E13: Slippage and transaction friction sensitivity (0 to 50 bps)."""
    try:
        return rr.cost_sensitivity()
    except rr.ResultsNotFound as e:
        raise HTTPException(status_code=404, detail={"error": "results_not_found", "message": str(e)})


@router.get("/stress-tests")
def stress_tests():
    """E14: Crash stress testing under historical shocks (COVID 2020, 2022 bear)."""
    try:
        return rr.stress_tests()
    except rr.ResultsNotFound as e:
        raise HTTPException(status_code=404, detail={"error": "results_not_found", "message": str(e)})


@router.get("/tournament")
def tournament():
    """E15: Out-of-sample championship tournament with bootstrap significance."""
    try:
        return rr.tournament_results()
    except rr.ResultsNotFound as e:
        raise HTTPException(status_code=404, detail={"error": "results_not_found", "message": str(e)})


@router.get("/backtest")
def backtest(experiment: Experiment = "E6"):
    try:
        return {
            "summary": rr.experiment_summary(experiment),
            "returns": rr.experiment_returns(experiment),
        }
    except rr.ResultsNotFound as e:
        raise HTTPException(status_code=404, detail={"error": "results_not_found", "message": str(e)})


@router.get("/backtest/weights")
def backtest_weights(experiment: Experiment = "E6"):
    try:
        return {"experiment": experiment, "weights": rr.experiment_weights(experiment)}
    except rr.ResultsNotFound as e:
        raise HTTPException(status_code=404, detail={"error": "results_not_found", "message": str(e)})
