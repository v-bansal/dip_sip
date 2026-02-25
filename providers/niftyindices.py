from __future__ import annotations

from providers.base import DataProvider, ProviderResult


class NiftyIndicesProvider(DataProvider):
    """Stub provider for NIFTY Indices historical download.

    Implement fetch_history() here when you are ready to wire the official download.
    Refer to: https://www.niftyindices.com/reports/historical-data
    """
    id = 'niftyindices_download'
    label = 'NIFTY Indices (stub)'

    def fetch_history(self, index_id: str, start_date=None, end_date=None, series_type: str = 'TRI') -> ProviderResult:
        raise NotImplementedError(
            'NiftyIndicesProvider is a stub. Implement download logic in providers/niftyindices.py.'
        )

    def fetch_latest(self, index_id: str, series_type: str = 'TRI') -> ProviderResult:
        return self.fetch_history(index_id, None, None, series_type)
