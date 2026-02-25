from __future__ import annotations

import pandas as pd


def make_contribution_dates(trading_days: pd.DatetimeIndex, schedule: str) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(trading_days)
    if schedule == 'daily':
        return idx
    if schedule == 'weekly':
        s = pd.Series(idx, index=idx)
        return pd.DatetimeIndex(s.groupby(idx.to_period('W')).max().values)
    if schedule == 'monthly':
        s = pd.Series(idx, index=idx)
        return pd.DatetimeIndex(s.groupby(idx.to_period('M')).max().values)
    raise ValueError('schedule must be daily/weekly/monthly')


def scale_amount_for_schedule(monthly_amount: float, schedule: str) -> float:
    """Scale per-contribution amount so annual total equals 12 x monthly_amount."""
    if schedule == 'monthly':
        return float(monthly_amount)
    if schedule == 'weekly':
        return float(monthly_amount) * 12.0 / 52.0
    if schedule == 'daily':
        return float(monthly_amount) * 12.0 / 252.0
    raise ValueError('schedule must be daily/weekly/monthly')
