from __future__ import annotations

import os
import yaml
import streamlit as st

from storage.cache import LocalCache


def load_yaml(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_DEFAULTS = os.path.join(BASE_DIR, 'config', 'defaults.yaml')
SCHEMA_SQL = os.path.join(BASE_DIR, 'storage', 'schema.sql')

cfg = load_yaml(CFG_DEFAULTS)
DB_PATH = cfg['storage']['cache_db_path']

cache = LocalCache(DB_PATH)
cache.init_db(SCHEMA_SQL)

st.set_page_config(page_title='Run Viewer — Dip-SIP', layout='wide')
st.title('Run Viewer')
st.caption('Enter a run_id (shown after saving a run on the Dashboard) to load and download its ledger.')

run_id = st.text_input('Enter run_id')

if run_id.strip():
    summary = cache.load_run_summary(run_id.strip())
    if not summary:
        st.warning('Run not found. Check the run_id.')
        st.stop()

    st.subheader('Summary')
    st.json(summary)

    st.subheader('Ledger')
    ledger = cache.load_ledger(run_id.strip())
    st.dataframe(ledger.tail(250), use_container_width=True)

    st.download_button(
        label='Download full ledger CSV',
        data=ledger.to_csv(index=False).encode('utf-8'),
        file_name=f'ledger_{run_id}.csv',
        mime='text/csv',
    )
