from typing import Optional
from pydantic import BaseModel, ConfigDict


class MetricSet(BaseModel):
    annual_return: Optional[float] = None
    volatility: Optional[float] = None
    sharpe: Optional[float] = None
    sortino: Optional[float] = None
    calmar: Optional[float] = None
    max_drawdown: Optional[float] = None
    turnover: Optional[float] = None


class ExperimentSummary(BaseModel):
    experiment: str
    period: str
    data_source: str
    synthetic: bool
    net: MetricSet
    gross: MetricSet


class Decision(BaseModel):
    """Champion-Challenger record. Extra fields (CI, metrics, dates) are kept as-is."""
    model_config = ConfigDict(extra="allow")
    date: str
    decision: str
    reason: Optional[str] = None


class PromotionLog(BaseModel):
    current_champion: Optional[str] = None
    counts: dict[str, int]
    accuracy_improved_but_rejected: int
    decisions: list[Decision]


# Legacy aliases kept for any code that imported them
class ExperimentMetrics(BaseModel):
    experiment: str
    annual_return: float
    volatility: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    turnover: float
    sharpe_gross: float


class ComparisonResponse(BaseModel):
    data_source: str
    synthetic: bool
    experiments: list[ExperimentMetrics]
    significance: Optional[dict] = None


class PortfolioHolding(BaseModel):
    symbol: str
    weight: float
    predicted_return: float
    risk_contribution: float
    diversification_benefit: bool
    max_cap_hit: bool


class PortfolioResponse(BaseModel):
    date: str
    strategy: str
    optimizer_version: str
    weights: list[PortfolioHolding]
    expected_return: float
    volatility: float
    sharpe: Optional[float] = None
    constraint_status: dict
