from __future__ import annotations

import os
import yaml
import streamlit as st
import streamlit_authenticator as stauth

from storage.cache_factory import get_cache


def load_yaml(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_DEFAULTS = os.path.join(BASE_DIR, 'config', 'defaults.yaml')
CFG_CREDENTIALS = os.path.join(BASE_DIR, 'config', 'credentials.yaml')
SCHEMA_SQL = os.path.join(BASE_DIR, 'storage', 'schema.sql')

cfg = load_yaml(CFG_DEFAULTS)
DB_PATH = cfg['storage']['cache_db_path']

st.set_page_config(page_title='Run Viewer — Dip-SIP', layout='wide')

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
