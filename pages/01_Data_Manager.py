from __future__ import annotations

import os
import yaml
import streamlit as st
import pandas as pd

from storage.cache import LocalCache
from providers.upload_csv import UploadCSVProvider


def load_yaml(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_DEFAULTS = os.path.join(BASE_DIR, 'config', 'defaults.yaml')
CFG_REGISTRY = os.path.join(BASE_DIR, 'config', 'index_registry.yaml')
SCHEMA_SQL = os.path.join(BASE_DIR, 'storage', 'schema.sql')

cfg = load_yaml(CFG_DEFAULTS)
registry = load_yaml(CFG_REGISTRY)

DB_PATH = cfg['storage']['cache_db_path']
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

cache = LocalCache(DB_PATH)
cache.init_db(SCHEMA_SQL)

st.set_page_config(page_title='Data Manager — Dip-SIP', layout='wide')
st.title('Data Manager')
st.caption('Upload your daily index CSV here to save it into the local cache. Then use the main Dashboard.')

indices = registry['indices']
index_label_to_id = {i['label']: i['index_id'] for i in indices}

col1, col2, col3 = st.columns(3)
with col1:
    index_label = st.selectbox('Index', list(index_label_to_id.keys()))
    index_id = index_label_to_id[index_label]
with col2:
    series_type = st.selectbox('Series type', ['TRI', 'PRICE'], index=0)
with col3:
    source_id = st.selectbox('Source', ['upload_csv'])

st.subheader('Upload CSV → cache')
uploaded = st.file_uploader('Upload daily CSV', type=['csv'])

cA, cB = st.columns(2)
with cA:
    date_col = st.text_input('Date column name', value='Date')
with cB:
    close_col = st.text_input('Close/TRI column name', value='Close')

if uploaded is not None:
    provider = UploadCSVProvider(uploaded, date_col=date_col, close_col=close_col)
    try:
        res = provider.fetch_history(index_id=index_id, series_type=series_type)
        df = res.df
        st.success(res.notes)
        st.write('Preview (first 20 rows):')
        st.dataframe(df.head(20), use_container_width=True)

        dfv = df.copy()
        dfv['date'] = pd.to_datetime(dfv['date'])
        st.write('Validation report:', {
            'rows': int(len(dfv)),
            'start_date': str(dfv['date'].min().date()),
            'end_date': str(dfv['date'].max().date()),
            'missing_close': int(dfv['close'].isna().sum()),
            'unique_dates': int(dfv['date'].nunique()),
        })

        if st.button('Save to local cache'):
            cache.upsert_prices(index_id=index_id, series_type=series_type, source_id=res.source_id, df=df)
            st.success(f'✅ Saved {len(df)} rows for {index_id} / {series_type} / {res.source_id}.')
            st.info('Return to the main Dashboard and select this cached source from the sidebar.')
    except Exception as e:
        st.error(str(e))

st.subheader('Currently cached sources')
for idx_spec in indices:
    iid = idx_spec['index_id']
    for st_type in ['TRI', 'PRICE']:
        srcs = cache.list_sources_for_index(iid, st_type)
        if srcs:
            st.write(f'**{idx_spec["label"]}** ({st_type}): {srcs}')
