from __future__ import annotations

import numpy as np
import pandas as pd


def xirr(cashflows, guess: float = 0.10) -> float:
    """Annualized IRR for irregular cashflows.

    cashflows: list of (date, amount) where contributions are negative
               and the final liquidation is positive.
    """
    if not cashflows or len(cashflows) < 2:
        return float('nan')

    dates = np.array([pd.Timestamp(d).to_datetime64() for d, _ in cashflows])
    amts = np.array([a for _, a in cashflows], dtype=float)
    t0 = dates.min()
    years = (dates - t0).astype('timedelta64[D]').astype(float) / 365.25

    def f(r):
        return np.sum(amts / np.power(1.0 + r, years))

    def fp(r):
        return np.sum(-years * amts / np.power(1.0 + r, years + 1.0))

    r = float(guess)
    for _ in range(200):
        y, dy = f(r), fp(r)
        if abs(dy) < 1e-14:
            break
        r_new = r - y / dy
        if not np.isfinite(r_new):
            break
        if abs(r_new - r) < 1e-11:
            r = r_new
            break
        r = r_new
    return float(r)
