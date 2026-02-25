-- Supabase schema for Dip-SIP app
-- Run this SQL in your Supabase project SQL Editor (https://app.supabase.com)

-- Table: prices (daily index price data)
CREATE TABLE IF NOT EXISTS prices (
  index_id    TEXT NOT NULL,
  series_type TEXT NOT NULL,
  source_id   TEXT NOT NULL,
  date        TEXT NOT NULL,
  close       REAL NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (index_id, series_type, source_id, date)
);

CREATE INDEX IF NOT EXISTS idx_prices_lookup
  ON prices(index_id, series_type, date);

-- Table: runs (backtest run metadata)
CREATE TABLE IF NOT EXISTS runs (
  run_id       TEXT PRIMARY KEY,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  index_id     TEXT NOT NULL,
  series_type  TEXT NOT NULL,
  source_id    TEXT NOT NULL,
  strategy_id  TEXT NOT NULL,
  plan_json    JSONB NOT NULL,
  params_json  JSONB NOT NULL,
  summary_json JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_created
  ON runs(created_at DESC);

-- Table: ledgers (day-by-day simulation results)
CREATE TABLE IF NOT EXISTS ledgers (
  run_id          TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
  date            TEXT NOT NULL,
  price           REAL NOT NULL,
  rolling_high    REAL NOT NULL,
  drawdown_pct    REAL NOT NULL,
  contribution    REAL NOT NULL,
  sip_buy         REAL NOT NULL,
  dip_base_buy    REAL NOT NULL,
  dip_trigger_buy REAL NOT NULL,
  dip_cash        REAL NOT NULL,
  sip_value       REAL NOT NULL,
  dip_value       REAL NOT NULL,
  PRIMARY KEY (run_id, date)
);

CREATE INDEX IF NOT EXISTS idx_ledgers_run
  ON ledgers(run_id, date);

-- Optional: Enable Row Level Security (RLS) if you want per-user data isolation
-- ALTER TABLE prices ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ledgers ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (adjust based on your auth setup):
-- CREATE POLICY "Users can only see their own data"
--   ON prices FOR ALL
--   USING (auth.uid() = user_id);  -- Add user_id column if needed
