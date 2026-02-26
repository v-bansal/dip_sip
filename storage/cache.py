from __future__ import annotations

import sqlite3
import json
import uuid
from datetime import datetime, timezone

import pandas as pd


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class LocalCache:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    def init_db(self, schema_sql_path: str):
        with open(schema_sql_path, 'r', encoding='utf-8') as f:
            schema = f.read()
        with self.connect() as con:
            con.executescript(schema)

    def upsert_prices(self, index_id: str, series_type: str, source_id: str, df: pd.DataFrame):
        dfx = df.copy()
        dfx['date'] = pd.to_datetime(dfx['date']).dt.date.astype(str)
        dfx = dfx.sort_values('date')
        rows = [
            (index_id, series_type, source_id, r['date'], float(r['close']), utc_now_iso())
            for _, r in dfx.iterrows()
        ]
        with self.connect() as con:
            con.executemany(
                'INSERT OR REPLACE INTO prices(index_id, series_type, source_id, date, close, updated_at) VALUES(?,?,?,?,?,?)',
                rows,
            )

    def load_prices(self, index_id: str, series_type: str, source_id: str) -> pd.DataFrame:
        with self.connect() as con:
            df = pd.read_sql_query(
                'SELECT date, close FROM prices WHERE index_id=? AND series_type=? AND source_id=? ORDER BY date ASC',
                con,
                params=(index_id, series_type, source_id),
            )
        return df

    def list_sources_for_index(self, index_id: str, series_type: str) -> list[str]:
        with self.connect() as con:
            cur = con.execute(
                'SELECT DISTINCT source_id FROM prices WHERE index_id=? AND series_type=? ORDER BY source_id ASC',
                (index_id, series_type),
            )
            return [r[0] for r in cur.fetchall()]

    def save_run(
        self,
        index_id: str,
        series_type: str,
        source_id: str,
        strategy_id: str,
        plan: dict,
        params: dict,
        summary: dict,
        ledger: pd.DataFrame,
    ) -> str:
        run_id = str(uuid.uuid4())
        created_at = utc_now_iso()
        with self.connect() as con:
            con.execute(
                'INSERT INTO runs(run_id, created_at, index_id, series_type, source_id, strategy_id, plan_json, params_json, summary_json) VALUES(?,?,?,?,?,?,?,?,?)',
                (run_id, created_at, index_id, series_type, source_id, strategy_id,
                 json.dumps(plan), json.dumps(params), json.dumps(summary)),
            )
            con.executemany(
                'INSERT OR REPLACE INTO ledgers(run_id, date, price, rolling_high, drawdown_pct, contribution, sip_buy, dip_base_buy, dip_trigger_buy, dip_cash, sip_value, dip_value) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                [
                    (run_id, r['date'], float(r['price']), float(r['rolling_high']),
                     float(r['drawdown_pct']), float(r['contribution']), float(r['sip_buy']),
                     float(r['dip_base_buy']), float(r['dip_trigger_buy']), float(r['dip_cash']),
                     float(r['sip_value']), float(r['dip_value']))
                    for _, r in ledger.iterrows()
                ],
            )
        return run_id

    def load_run_summary(self, run_id: str) -> dict:
        with self.connect() as con:
            row = con.execute('SELECT summary_json FROM runs WHERE run_id=?', (run_id,)).fetchone()
        return json.loads(row[0]) if row else {}

    def load_ledger(self, run_id: str) -> pd.DataFrame:
        with self.connect() as con:
            df = pd.read_sql_query(
                'SELECT date, price, rolling_high, drawdown_pct, contribution, sip_buy, dip_base_buy, dip_trigger_buy, dip_cash, sip_value, dip_value FROM ledgers WHERE run_id=? ORDER BY date ASC',
                con,
                params=(run_id,),
            )
        return df
