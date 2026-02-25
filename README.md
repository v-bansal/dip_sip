# Dip-SIP Local (Streamlit)

Local-only Streamlit application for:
- Index selection (NIFTY 50 / Next 50 / IT / Pharma, extendable)
- Data ingestion and caching (CSV upload + pluggable providers)
- Dip-SIP trigger generation (daily band-entry) + cash bucket tracking
- Backtest comparison vs Standard SIP (terminal value + XIRR)
- Exports (ledger CSV + summary JSON)

## Quick start (local)

```bash
cd dip_sip
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Data input

The app expects daily data with at least:
- Date (YYYY-MM-DD)
- Close (index level; TRI preferred)

Use the **Data Manager** page to upload CSV and save it into the local cache.

## Notes on data providers

- `upload_csv` works offline.
- `niftyindices_download` and `nse_historical_index` are included as **stubs** (interfaces + caching hooks)
  because official endpoints/formats can change; implement them in `providers/` when you decide
  the exact retrieval method you trust.

## Local cache

SQLite file: `./data/cache.sqlite`

Tables:
- `prices` (normalized daily series)
- `runs` (backtest runs + parameters)
- `ledgers` (day-by-day ledger for a run)
