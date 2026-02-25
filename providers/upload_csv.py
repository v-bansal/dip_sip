from __future__ import annotations

import pandas as pd

from providers.base import DataProvider, ProviderResult


class UploadCSVProvider(DataProvider):
    id = 'upload_csv'
    label = 'Upload CSV'

    def __init__(self, uploaded_file, date_col: str = 'Date', close_col: str = 'Close'):
        self.uploaded_file = uploaded_file
        self.date_col = date_col
        self.close_col = close_col

    def fetch_history(self, index_id: str, start_date=None, end_date=None, series_type: str = 'TRI') -> ProviderResult:
        df = pd.read_csv(self.uploaded_file)
        if self.date_col not in df.columns or self.close_col not in df.columns:
            raise ValueError(
                f"CSV must contain {self.date_col!r} and {self.close_col!r}. Found: {list(df.columns)}"
            )
        dfx = df[[self.date_col, self.close_col]].copy()
        dfx.columns = ['date', 'close']
        dfx['date'] = pd.to_datetime(dfx['date']).dt.date.astype(str)
        dfx['close'] = dfx['close'].astype(float)
        dfx = dfx.dropna().sort_values('date').reset_index(drop=True)
        if start_date:
            dfx = dfx[dfx['date'] >= str(start_date)]
        if end_date:
            dfx = dfx[dfx['date'] <= str(end_date)]
        return ProviderResult(df=dfx, source_id=self.id, series_type=series_type, notes='Loaded from uploaded CSV')

    def fetch_latest(self, index_id: str, series_type: str = 'TRI') -> ProviderResult:
        return self.fetch_history(index_id, None, None, series_type)
