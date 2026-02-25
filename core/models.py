from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

SeriesType = Literal['TRI', 'PRICE']
Schedule = Literal['daily', 'weekly', 'monthly']


@dataclass
class Plan:
    plan_mode: Literal['monthly_amount', 'yearly_amount_spread_monthly']
    monthly_amount_inr: float
    yearly_amount_inr: float
    schedule: Schedule


@dataclass
class StrategyConfig:
    strategy_id: Literal['dip_sip_band_entry']
    lookback_days: int
    base_fraction: float
    thresholds_pct: List[float]
    deploy_fractions: List[float]
    allow_daily_dip_buys: bool
    transaction_cost_bps: float
    cash_rate_annual: float


@dataclass
class BacktestSummary:
    total_contributed: float
    sip_final: float
    dip_final: float
    sip_xirr: float
    dip_xirr: float
    alpha_xirr: float
    sip_trades: int
    dip_trades: int
