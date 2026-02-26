from __future__ import annotations

import io
from datetime import datetime, timedelta
import pandas as pd
import requests

from providers.base import DataProvider, ProviderResult


class NiftyIndicesProvider(DataProvider):
    """Auto-fetch provider for NIFTY Indices historical data.
    
    Downloads TRI (Total Returns Index) or Price data directly from niftyindices.com.
    """
    
    id = 'niftyindices_download'
    label = 'NIFTY Indices (Auto-fetch)'
    
    # Mapping from app index_id to NIFTY Indices official names
    INDEX_MAPPING = {
        'NIFTY50': 'NIFTY 50',
        'NIFTY_NEXT_50': 'NIFTY NEXT 50',
        'NIFTY_IT': 'NIFTY IT',
        'NIFTY_PHARMA': 'NIFTY PHARMA',
        'NIFTY_BANK': 'NIFTY BANK',
        'NIFTY_AUTO': 'NIFTY AUTO',
        'NIFTY_FMCG': 'NIFTY FMCG',
        'NIFTY_METAL': 'NIFTY METAL',
        'NIFTY_REALTY': 'NIFTY REALTY',
        'NIFTY_ENERGY': 'NIFTY ENERGY',
        'NIFTY_INFRA': 'NIFTY INFRASTRUCTURE',
        'NIFTY_PSU_BANK': 'NIFTY PSU BANK',
    }
    
    BASE_URL = 'https://www.niftyindices.com/IndexArchive'
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
    
    def _get_index_name(self, index_id: str) -> str:
        """Convert app index_id to NIFTY Indices official name."""
        return self.INDEX_MAPPING.get(index_id, index_id)
    
    def _build_download_params(self, index_name: str, start_date: str, end_date: str, series_type: str) -> dict:
        """Build URL parameters for NIFTY Indices download."""
        index_type = 'TRI' if series_type == 'TRI' else 'Total Returns Index'
        
        return {
            'name': index_name,
            'indexType': index_type,
            'fromDate': start_date,
            'toDate': end_date,
        }
    
    def _parse_date(self, date_str: str) -> str:
        """Convert YYYY-MM-DD to dd-MM-yyyy for NIFTY Indices API."""
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%d-%m-%Y')
        except:
            return date_str
    
    def fetch_history(
        self,
        index_id: str,
        start_date: str = None,
        end_date: str = None,
        series_type: str = 'TRI'
    ) -> ProviderResult:
        """Fetch historical data from NIFTY Indices.
        
        Args:
            index_id: App index ID (e.g., 'NIFTY50')
            start_date: Start date in YYYY-MM-DD format (default: 3 years ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            series_type: 'TRI' or 'PRICE'
        
        Returns:
            ProviderResult with DataFrame containing date, close columns
        """
        index_name = self._get_index_name(index_id)
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_dt = datetime.now() - timedelta(days=3*365)
            start_date = start_dt.strftime('%Y-%m-%d')
        
        start_formatted = self._parse_date(start_date)
        end_formatted = self._parse_date(end_date)
        
        params = self._build_download_params(index_name, start_formatted, end_formatted, series_type)
        
        try:
            url = f"{self.BASE_URL}/histidxdata"
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            df = pd.read_csv(io.StringIO(response.text))
            df.columns = df.columns.str.strip()
            
            if 'Date' not in df.columns:
                raise ValueError(f"CSV missing 'Date' column. Found: {list(df.columns)}")
            
            close_col = 'Close'
            if 'Close' not in df.columns:
                for col in ['Close*', 'Closing Index Value', 'Close Value']:
                    if col in df.columns:
                        close_col = col
                        break
            
            if close_col not in df.columns:
                raise ValueError(f"CSV missing 'Close' column. Found: {list(df.columns)}")
            
            dfx = df[['Date', close_col]].copy()
            dfx.columns = ['date', 'close']
            
            dfx['date'] = pd.to_datetime(dfx['date'], format='%d-%b-%Y', errors='coerce')
            dfx = dfx.dropna(subset=['date'])
            dfx['date'] = dfx['date'].dt.date.astype(str)
            
            dfx['close'] = dfx['close'].astype(str).str.replace(',', '').astype(float)
            dfx = dfx.sort_values('date').drop_duplicates(subset=['date'], keep='last').reset_index(drop=True)
            
            return ProviderResult(
                df=dfx,
                source_id=self.id,
                series_type=series_type,
                notes=f'Fetched {len(dfx)} rows from NIFTY Indices for {index_name} ({series_type})'
            )
            
        except requests.RequestException as e:
            raise ConnectionError(
                f"Failed to download from NIFTY Indices. Error: {str(e)}. "
                f"Try manual download from https://www.niftyindices.com/reports/historical-data"
            )
        except Exception as e:
            raise ValueError(
                f"Failed to parse NIFTY Indices data. Error: {str(e)}. "
                f"The website format may have changed. Please report this issue."
            )
    
    def fetch_latest(self, index_id: str, series_type: str = 'TRI') -> ProviderResult:
        """Fetch latest available data (last 30 days)."""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        return self.fetch_history(index_id, start_date, end_date, series_type)
