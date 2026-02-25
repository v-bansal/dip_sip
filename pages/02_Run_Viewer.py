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
authenticator = stauth.Authenticate(
    credentials=load_yaml(CFG_CREDENTIALS),
    cookie_name=st.secrets.get('auth_cookie_name', 'dip_sip_auth'),
    key=st.secrets.get('auth_cookie_key', 'default_key'),
    cookie_expiry_days=int(st.secrets.get('auth_cookie_expiry_days', 30)),
)

name, authentication_status, username = authenticator.login('Login', 'sidebar')

if authentication_status == False:
    st.error('Username/password is incorrect')
    st.stop()

if authentication_status == None:
    st.warning('Please enter your username and password')
    st.stop()

authenticator.logout('Logout', 'sidebar')
st.sidebar.write(f'Welcome, **{name}**')

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
