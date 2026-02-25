-- Local cache schema for Dip-SIP app

CREATE TABLE IF NOT EXISTS prices (
  index_id    TEXT NOT NULL,
  series_type TEXT NOT NULL,
  source_id   TEXT NOT NULL,
  date        TEXT NOT NULL,
  close       REAL NOT NULL,
  updated_at  TEXT NOT NULL,
  PRIMARY KEY (index_id, series_type, source_id, date)
);

CREATE INDEX IF NOT EXISTS idx_prices_lookup
  ON prices(index_id, series_type, date);

CREATE TABLE IF NOT EXISTS runs (
  run_id       TEXT PRIMARY KEY,
  created_at   TEXT NOT NULL,
  index_id     TEXT NOT NULL,
  series_type  TEXT NOT NULL,
  source_id    TEXT NOT NULL,
  strategy_id  TEXT NOT NULL,
  plan_json    TEXT NOT NULL,
  params_json  TEXT NOT NULL,
  summary_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ledgers (
  run_id          TEXT NOT NULL,
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
