from __future__ import annotations

import pandas as pd
import numpy as np

from core.xirr import xirr
from core.calendar import make_contribution_dates
from core.models import BacktestSummary


def normalize_price_series(df: pd.DataFrame, date_col: str, close_col: str) -> pd.Series:
    dfx = df.copy()
    dfx[date_col] = pd.to_datetime(dfx[date_col])
    dfx = dfx.sort_values(date_col).dropna(subset=[close_col])
    s = pd.Series(
        dfx[close_col].astype(float).values,
        index=pd.DatetimeIndex(dfx[date_col]),
    )
    return s[~s.index.duplicated(keep='last')]


def drawdown_from_rolling_high(prices: pd.Series, lookback_days: int):
    roll_max = prices.rolling(int(lookback_days), min_periods=1).max()
    dd = (prices / roll_max - 1.0) * 100.0
    return dd, roll_max


def run_backtest(
    prices: pd.Series,
    schedule: str,
    amount_per_contrib: float,
    lookback_days: int,
    base_fraction: float,
    thresholds_pct: list[float],
    deploy_fractions: list[float],
    allow_daily_dip_buys: bool,
    transaction_cost_bps: float,
    cash_rate_annual: float,
) -> tuple[BacktestSummary, pd.DataFrame]:
    thresholds = [float(x) for x in thresholds_pct]
    deploy = [float(x) for x in deploy_fractions]
    if len(thresholds) != len(deploy):
        raise ValueError('thresholds_pct and deploy_fractions must have same length')

    idx = pd.DatetimeIndex(prices.index)
    contrib_dates = set(make_contribution_dates(idx, schedule))
    dd, roll_max = drawdown_from_rolling_high(prices, lookback_days)

    # Standard SIP state
    sip_units = 0.0
    sip_total = 0.0
    sip_trades = 0
    sip_cfs = []

    # Dip-SIP state
    dip_units = 0.0
    dip_cash = 0.0
    dip_total = 0.0
    dip_trades = 0
    dip_cfs = []

    daily_rate = (1.0 + float(cash_rate_annual)) ** (1.0 / 365.25) - 1.0
    last_date = idx[0]
    min_band = -1  # deepest band entered since last re-arm

    rows = []

    def band_from_dd(dd_value: float) -> int:
        level = -1
        for i, t in enumerate(thresholds):
            if dd_value <= -t:
                level = i
        return level

    for d in idx:
        p = float(prices.loc[d])

        # Accrue dip cash between dates
        days = (pd.Timestamp(d) - pd.Timestamp(last_date)).days
        if days > 0 and dip_cash > 0:
            dip_cash *= (1.0 + daily_rate) ** days
        last_date = d

        contribution = float(amount_per_contrib) if d in contrib_dates else 0.0

        # Standard SIP
        sip_buy = 0.0
        if contribution > 0:
            fee = contribution * (transaction_cost_bps / 1e4)
            sip_units += (contribution - fee) / p
            sip_total += contribution
            sip_trades += 1
            sip_cfs.append((d, -contribution))
            sip_buy = contribution
            dip_cash += contribution
            dip_total += contribution
            dip_cfs.append((d, -contribution))

        cur_dd = float(dd.loc[d])

        # Re-arm when at rolling high
        if cur_dd >= -1e-12:
            min_band = -1

        # Baseline buy on contribution day
        dip_base_buy = 0.0
        if contribution > 0 and base_fraction > 0 and dip_cash > 0:
            invest = dip_cash * float(base_fraction)
            fee = invest * (transaction_cost_bps / 1e4)
            dip_units += (invest - fee) / p
            dip_cash -= invest
            dip_trades += 1
            dip_base_buy = invest

        # Dip trigger buy on band entry
        dip_trigger_buy = 0.0
        is_action_day = True if allow_daily_dip_buys else (d in contrib_dates)
        if is_action_day and dip_cash > 0:
            level = band_from_dd(cur_dd)
            if level > min_band:
                deploy_amt = dip_cash * deploy[level]
                fee = deploy_amt * (transaction_cost_bps / 1e4)
                dip_units += (deploy_amt - fee) / p
                dip_cash -= deploy_amt
                dip_trades += 1
                dip_trigger_buy = deploy_amt
                min_band = level

        rows.append({
            'date': d.date().isoformat(),
            'price': p,
            'rolling_high': float(roll_max.loc[d]),
            'drawdown_pct': cur_dd,
            'contribution': contribution,
            'sip_buy': sip_buy,
            'dip_base_buy': dip_base_buy,
            'dip_trigger_buy': dip_trigger_buy,
            'dip_cash': dip_cash,
            'sip_value': sip_units * p,
            'dip_value': dip_units * p + dip_cash,
        })

    end = idx[-1]
    sip_final = float(sip_units * float(prices.iloc[-1]))
    dip_final = float(dip_units * float(prices.iloc[-1]) + dip_cash)
    sip_cfs.append((end, sip_final))
    dip_cfs.append((end, dip_final))

    return BacktestSummary(
        total_contributed=float(sip_total),
        sip_final=sip_final,
        dip_final=dip_final,
        sip_xirr=float(xirr(sip_cfs)),
        dip_xirr=float(xirr(dip_cfs)),
        alpha_xirr=float(xirr(dip_cfs) - xirr(sip_cfs)),
        sip_trades=int(sip_trades),
        dip_trades=int(dip_trades),
    ), pd.DataFrame(rows)
