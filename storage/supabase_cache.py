from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pandas as pd
from supabase import create_client, Client


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class SupabaseCache:
    """Drop-in replacement for LocalCache that uses Supabase Postgres."""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)

    def init_db(self, schema_sql_path: str = None):
        """No-op: Supabase tables are created via SQL console or migration.
        
        Run the SQL in storage/supabase_schema.sql in your Supabase SQL Editor.
        """
        pass

    def upsert_prices(self, index_id: str, series_type: str, source_id: str, df: pd.DataFrame):
        dfx = df.copy()
        dfx['date'] = pd.to_datetime(dfx['date']).dt.date.astype(str)
        dfx = dfx.sort_values('date')
        
        rows = [
            {
                'index_id': index_id,
                'series_type': series_type,
                'source_id': source_id,
                'date': r['date'],
                'close': float(r['close']),
                'updated_at': utc_now_iso(),
            }
            for _, r in dfx.iterrows()
        ]
        
        # Supabase upsert (on conflict do update)
        self.client.table('prices').upsert(rows, on_conflict='index_id,series_type,source_id,date').execute()

    def load_prices(self, index_id: str, series_type: str, source_id: str) -> pd.DataFrame:
        response = (
            self.client.table('prices')
            .select('date, close')
            .eq('index_id', index_id)
            .eq('series_type', series_type)
            .eq('source_id', source_id)
            .order('date')
            .execute()
        )
        return pd.DataFrame(response.data)

    def list_sources_for_index(self, index_id: str, series_type: str) -> list[str]:
    print(f"DEBUG: Querying index_id='{index_id}', series_type='{series_type}'")  # ADD THIS
    
    response = (
        self.client.table('prices')
        .select('source_id, index_id, series_type')  # ADD index_id, series_type
        .eq('index_id', index_id)
        .eq('series_type', series_type)
        .limit(5)  # Limit for debug
        .execute()
    )
    
    print(f"DEBUG: Raw Supabase response: {response.data}")  # ADD THIS
    
    sources = list(set(r['source_id'] for r in response.data))
    print(f"DEBUG: Extracted sources: {sources}")  # ADD THIS
    return sorted(sources)


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
        
        # Insert run metadata
        self.client.table('runs').insert({
            'run_id': run_id,
            'created_at': created_at,
            'index_id': index_id,
            'series_type': series_type,
            'source_id': source_id,
            'strategy_id': strategy_id,
            'plan_json': json.dumps(plan),
            'params_json': json.dumps(params),
            'summary_json': json.dumps(summary),
        }).execute()
        
        # Insert ledger rows
        ledger_rows = [
            {
                'run_id': run_id,
                'date': r['date'],
                'price': float(r['price']),
                'rolling_high': float(r['rolling_high']),
                'drawdown_pct': float(r['drawdown_pct']),
                'contribution': float(r['contribution']),
                'sip_buy': float(r['sip_buy']),
                'dip_base_buy': float(r['dip_base_buy']),
                'dip_trigger_buy': float(r['dip_trigger_buy']),
                'dip_cash': float(r['dip_cash']),
                'sip_value': float(r['sip_value']),
                'dip_value': float(r['dip_value']),
            }
            for _, r in ledger.iterrows()
        ]
        
        # Batch insert (Supabase allows up to 1000 rows per insert)
        batch_size = 1000
        for i in range(0, len(ledger_rows), batch_size):
            batch = ledger_rows[i:i + batch_size]
            self.client.table('ledgers').insert(batch).execute()
        
        return run_id

    def load_run_summary(self, run_id: str) -> dict:
        response = (
            self.client.table('runs')
            .select('summary_json')
            .eq('run_id', run_id)
            .execute()
        )
        if response.data:
            return json.loads(response.data[0]['summary_json'])
        return {}

    def load_ledger(self, run_id: str) -> pd.DataFrame:
        response = (
            self.client.table('ledgers')
            .select('date, price, rolling_high, drawdown_pct, contribution, sip_buy, dip_base_buy, dip_trigger_buy, dip_cash, sip_value, dip_value')
            .eq('run_id', run_id)
            .order('date')
            .execute()
        )
        return pd.DataFrame(response.data)
