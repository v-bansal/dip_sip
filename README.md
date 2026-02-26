# Dip-SIP Local (Streamlit)

Local-only **or** cloud-hosted Streamlit application for:
- Index selection (NIFTY 50 / Next 50 / IT / Pharma, extendable)
- Data ingestion and caching (CSV upload + pluggable providers)
- Dip-SIP trigger generation (daily band-entry) + cash bucket tracking
- Backtest comparison vs Standard SIP (terminal value + XIRR)
- Exports (ledger CSV + summary JSON)
- **User authentication** (login/logout)
- **Supabase storage** (persistent online) or **SQLite** (local-only)

---

## Quick start (local — Mac/Linux)

```bash
git clone -b dev https://github.com/v-bansal/dip_sip.git
cd dip_sip
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure secrets (optional for local SQLite)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml and set auth_cookie_key

streamlit run app.py
```

Default login (change in `config/credentials.yaml`):
- **Username:** `admin` | **Password:** `admin123`
- **Username:** `viewer` | **Password:** `viewer123`

---

## Quick start (online — Streamlit Community Cloud)

### 1. Create Supabase project
1. Go to [supabase.com](https://supabase.com) → New project
2. Open **SQL Editor** → paste `storage/supabase_schema.sql` → Run
3. Go to **Settings → API** → copy `URL` and `anon public` key

### 2. Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. New app → Select `v-bansal/dip_sip`, branch `dev`, file `app.py`
3. Click **Advanced settings** → **Secrets** → paste:
   ```toml
   auth_cookie_name = "dip_sip_auth"
   auth_cookie_key = "your_random_32char_key"  # Generate: python -c "import secrets; print(secrets.token_hex(16))"
   auth_cookie_expiry_days = 30
   SUPABASE_URL = "https://xxx.supabase.co"
   SUPABASE_KEY = "your-anon-key"
   ```
4. Deploy → Your app is live with authentication + persistent storage

---

## Data input

The app expects daily data with:
- **Date** (YYYY-MM-DD)
- **Close** (index level; TRI preferred)

Use the **Data Manager** page to upload CSV and save it into the cache.

---

## Architecture

### Local mode (SQLite)
- Runs on your Mac/laptop
- Data stored in `./data/cache.sqlite`
- No internet needed after setup

### Online mode (Supabase)
- Runs on Streamlit Cloud
- Data stored in Supabase Postgres (persistent across deploys)
- Access from anywhere
- Multi-user capable

### Auto-detection
The app automatically uses:
- **Supabase** if `SUPABASE_URL` exists in `.streamlit/secrets.toml`
- **SQLite** otherwise (local development)

---

## Authentication

### Change passwords
Edit `config/credentials.yaml`. Generate bcrypt hashes:
```bash
python -c "import bcrypt; print(bcrypt.hashpw('yourpassword'.encode(), bcrypt.gensalt()).decode())"
```

### Add users
Add to `config/credentials.yaml`:
```yaml
credentials:
  usernames:
    newuser:
      email: user@example.com
      name: New User
      password: $2b$12$...  # bcrypt hash
```

---

## Providers (data sources)

- ✅ **CSV upload** — works offline (implemented)
- 🚧 **NIFTY Indices download** — stub (implement in `providers/niftyindices.py`)
- 🚧 **NSE Historical Index** — stub (implement in `providers/nse.py`)
- 🚧 **SmartAPI / Breeze** — stubs (for broker APIs)

---

## Local cache tables

### SQLite (local)
- `prices` (normalized daily series)
- `runs` (backtest runs + parameters)
- `ledgers` (day-by-day ledger for a run)

### Supabase (online)
Same schema, created via `storage/supabase_schema.sql`

---

## Files

| Path | What it is |
|---|---|
| `app.py` | Main dashboard with auth |
| `pages/01_Data_Manager.py` | CSV upload → cache |
| `pages/02_Run_Viewer.py` | Saved run viewer |
| `core/engine.py` | Backtest engine |
| `storage/cache.py` | SQLite adapter |
| `storage/supabase_cache.py` | Supabase adapter |
| `storage/cache_factory.py` | Auto-selects SQLite or Supabase |
| `config/credentials.yaml` | User logins (bcrypt hashed) |
| `config/index_registry.yaml` | Index list |
| `config/defaults.yaml` | Strategy defaults |

---

## Troubleshooting

### Local

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: streamlit_authenticator` | Run `pip install -r requirements.txt` |
| `KeyError: 'auth_cookie_key'` | Create `.streamlit/secrets.toml` from example |
| Login fails | Check `config/credentials.yaml` passwords |

### Online (Streamlit Cloud)

| Problem | Fix |
|---|---|
| `Unable to connect to Supabase` | Check `SUPABASE_URL` and `SUPABASE_KEY` in secrets |
| Tables don't exist | Run `storage/supabase_schema.sql` in Supabase SQL Editor |
| Data not persisting | Confirm you're using Supabase, not SQLite |

---

## Next steps

1. Change default passwords in `config/credentials.yaml`
2. Deploy to Streamlit Cloud with Supabase
3. Implement auto-fetch providers (`niftyindices.py` or `nse.py`)
4. Add more indices in `config/index_registry.yaml`
5. Customize strategy defaults in `config/defaults.yaml`
