from __future__ import annotations

from providers.base import DataProvider, ProviderResult


class NSEHistoricalIndexProvider(DataProvider):
    """Stub provider for NSE Historical Index Data.

    Implement fetch_history() here when you are ready to wire the official download.
    Refer to: https://www.nseindia.com/reports-indices-historical-index-data
    """
    id = 'nse_historical_index'
    label = 'NSE Historical Index (stub)'

    def fetch_history(self, index_id: str, start_date=None, end_date=None, series_type: str = 'TRI') -> ProviderResult:
        raise NotImplementedError(
            'NSEHistoricalIndexProvider is a stub. Implement download logic in providers/nse.py.'
        )

    def fetch_latest(self, index_id: str, series_type: str = 'TRI') -> ProviderResult:
        return self.fetch_history(index_id, None, None, series_type)
