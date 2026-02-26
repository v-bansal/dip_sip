from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass
class ProviderResult:
    df: pd.DataFrame       # columns: date (str YYYY-MM-DD), close (float)
    source_id: str
    series_type: str       # TRI or PRICE
    notes: str = ''


class DataProvider:
    id: str = ''
    label: str = ''

    def fetch_history(self, index_id: str, start_date, end_date, series_type: str) -> ProviderResult:
        raise NotImplementedError

    def fetch_latest(self, index_id: str, series_type: str) -> ProviderResult:
        raise NotImplementedError
