from __future__ import annotations

import os
import yaml
import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from datetime import datetime, timedelta

from storage.cache_factory import get_cache
from providers.upload_csv import UploadCSVProvider
from providers.niftyindices import NiftyIndicesProvider


def load_yaml(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_DEFAULTS = os.path.join(BASE_DIR, 'config', 'defaults.yaml')
CFG_REGISTRY = os.path.join(BASE_DIR, 'config', 'index_registry.yaml')
CFG_CREDENTIALS = os.path.join(BASE_DIR, 'config', 'credentials.yaml')
SCHEMA_SQL = os.path.join(BASE_DIR, 'storage', 'schema.sql')

cfg = load_yaml(CFG_DEFAULTS)
registry = load_yaml(CFG_REGISTRY)

DB_PATH = cfg['storage']['cache_db_path']
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

st.set_page_config(page_title='Data Manager — Dip-SIP', layout='wide')

# ========== AUTHENTICATION ==========
cfg_credentials = yaml.safe_load(open(CFG_CREDENTIALS, 'r', encoding='utf-8'))

authenticator = stauth.Authenticate(
    cfg_credentials['credentials'],
    cfg_credentials['cookie']['name'],
    cfg_credentials['cookie']['key'],
    cfg_credentials['cookie']['expiry_days']
)

authenticator.login(location='sidebar')

if 'authentication_status' not in st.session_state:
    st.session_state.authentication_status = None

if st.session_state.authentication_status == False:
    st.error('❌ Username/password is incorrect')
    st.stop()

elif st.session_state.authentication_status == None:
    st.sidebar.title('🔐 Login')
    st.stop()

name = st.session_state['name']
st.sidebar.success(f'👋 Logged in as **{name}**')
authenticator.logout('Logout', 'sidebar')


# ========== INITIALIZE CACHE ==========
cache = get_cache(DB_PATH)
cache.init_db(SCHEMA_SQL)

st.title('Data Manager')
st.caption('Import index data via CSV upload or auto-fetch from NIFTY Indices.')

indices = registry['indices']
index_label_to_id = {i['label']: i['index_id'] for i in indices}

col1, col2, col3 = st.columns(3)
with col1:
    index_label = st.selectbox('Index', list(index_label_to_id.keys()))
    index_id = index_label_to_id[index_label]
with col2:
    series_type = st.selectbox('Series type', ['TRI', 'PRICE'], index=0)
with col3:
    source_id = st.selectbox('Source', ['upload_csv', 'niftyindices_download'])

st.markdown('---')

if source_id == 'upload_csv':
    st.subheader('📁 Upload CSV → cache')
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
            
            if st.button('💾 Save to cache'):
                cache.upsert_prices(index_id=index_id, series_type=series_type, source_id=res.source_id, df=df)
                st.success(f'✅ Saved {len(df)} rows for {index_id} / {series_type} / {res.source_id}.')
                st.info('Return to the main Dashboard and select this cached source from the sidebar.')
        except Exception as e:
            st.error(str(e))

elif source_id == 'niftyindices_download':
    st.subheader('🌐 Auto-fetch from NIFTY Indices')
    st.caption('Downloads data directly from niftyindices.com (official NSE source)')
    
    # Date range selector
    col_a, col_b = st.columns(2)
    with col_a:
        default_start = datetime.now() - timedelta(days=3*365)
        start_date = st.date_input('Start date', value=default_start)
    with col_b:
        end_date = st.date_input('End date', value=datetime.now())
    
    st.info(f'Will fetch data for: **{index_label}** ({series_type}) from {start_date} to {end_date}')
    
    if st.button('🚀 Fetch and save to cache'):
        with st.spinner('Downloading from NIFTY Indices...'):
            try:
                provider = NiftyIndicesProvider()
                res = provider.fetch_history(
                    index_id=index_id,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    series_type=series_type,
                )
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
                
                # Auto-save
                cache.upsert_prices(index_id=index_id, series_type=series_type, source_id=res.source_id, df=df)
                st.success(f'✅ Saved {len(df)} rows to cache. Go to Dashboard and select this source.')
                
            except Exception as e:
                st.error(f'❌ Failed to fetch data: {str(e)}')
                st.info('💡 Tip: Try manual download from https://www.niftyindices.com/reports/historical-data')

st.markdown('---')
st.subheader('📊 Currently cached sources')
for idx_spec in indices:
    iid = idx_spec['index_id']
    for st_type in ['TRI', 'PRICE']:
        srcs = cache.list_sources_for_index(iid, st_type)
        if srcs:
            st.write(f'**{idx_spec["label"]}** ({st_type}): {srcs}')
