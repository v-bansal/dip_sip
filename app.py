from __future__ import annotations

import os
import json
import yaml
import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth

from storage.cache_factory import get_cache
from core.engine import normalize_price_series, run_backtest
from core.calendar import scale_amount_for_schedule


def load_yaml(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def ensure_dirs(p: str):
    os.makedirs(p, exist_ok=True)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_DEFAULTS = os.path.join(BASE_DIR, 'config', 'defaults.yaml')
CFG_REGISTRY = os.path.join(BASE_DIR, 'config', 'index_registry.yaml')
CFG_CREDENTIALS = os.path.join(BASE_DIR, 'config', 'credentials.yaml')
SCHEMA_SQL = os.path.join(BASE_DIR, 'storage', 'schema.sql')

cfg = load_yaml(CFG_DEFAULTS)
registry = load_yaml(CFG_REGISTRY)

DB_PATH = cfg['storage']['cache_db_path']
EXPORTS_DIR = cfg['storage']['exports_dir']

ensure_dirs(os.path.dirname(DB_PATH))
ensure_dirs(EXPORTS_DIR)

st.set_page_config(page_title='Dip-SIP Local', layout='wide')

# ========== AUTHENTICATION ==========
cfg_credentials = yaml.safe_load(open(CFG_CREDENTIALS, 'r', encoding='utf-8'))

authenticator = stauth.Authenticate(
    cfg_credentials['credentials'],
    cfg_credentials['cookie']['name'],
    cfg_credentials['cookie']['key'],
    cfg_credentials['cookie']['expiry_days']
)

# Render login form
authenticator.login(location='main')

# Check session state (set by login widget)
if 'authentication_status' not in st.session_state:
    st.session_state.authentication_status = None

if st.session_state.authentication_status == False:
    st.error('❌ Username/password is incorrect')
    st.stop()

elif st.session_state.authentication_status == None:
    st.title('🔐 Dip-SIP Login')
    st.stop()

# User authenticated ✅
name = st.session_state['name']
st.sidebar.success(f'👋 Logged in as **{name}**')
authenticator.logout('Logout', 'sidebar')



# ========== INITIALIZE CACHE ==========
cache = get_cache(DB_PATH)
cache.init_db(SCHEMA_SQL)

st.title('Dip-SIP — Triggers + Backtest')

indices = registry['indices']
index_label_to_id = {i['label']: i['index_id'] for i in indices}

with st.sidebar:
    st.header('Index')
    index_label = st.selectbox('Select index', list(index_label_to_id.keys()))
    index_id = index_label_to_id[index_label]

    st.header('Data source')
    series_type = st.selectbox('Series type', ['TRI', 'PRICE'], index=0)

    sources = cache.list_sources_for_index(index_id, series_type)
    if sources:
        source_id = st.selectbox('Cached source', sources)
    else:
        source_id = None
        st.warning('No cached data found. Go to Data Manager page to upload and cache data.')

    st.header('Plan')
    plan_mode = st.selectbox(
        'Plan mode',
        ['monthly_amount', 'yearly_amount_spread_monthly'],
        index=0 if cfg['plan_defaults']['plan_mode'] == 'monthly_amount' else 1,
    )
    if plan_mode == 'monthly_amount':
        monthly_amount = st.number_input(
            'Monthly contribution (₹)',
            min_value=0.0,
            value=float(cfg['plan_defaults']['monthly_amount_inr']),
            step=1000.0,
        )
        yearly_amount = monthly_amount * 12.0
    else:
        yearly_amount = st.number_input(
            'Yearly contribution (₹)',
            min_value=0.0,
            value=float(cfg['plan_defaults']['yearly_amount_inr']),
            step=10000.0,
        )
        monthly_amount = yearly_amount / 12.0
        st.caption(f'Implied monthly: ₹{monthly_amount:,.2f}')

    schedule = st.selectbox(
        'Contribution schedule',
        ['monthly', 'weekly', 'daily'],
        index=['monthly', 'weekly', 'daily'].index(cfg['plan_defaults']['schedule']),
    )

    st.header('Strategy (Dip-SIP)')
    dflt = cfg['strategy_defaults']
    lookback = st.number_input('Rolling-high lookback (trading days)', min_value=20, value=int(dflt['lookback_days']), step=10)
    base_fraction = st.slider('Base fraction (invest on contribution day)', 0.0, 0.8, float(dflt['base_fraction']), 0.01)
    thresholds_str = st.text_input('Dip thresholds (% drawdown)', value=','.join(map(str, dflt['thresholds_pct'])))
    deploy_str = st.text_input('Deploy fractions (remaining cash)', value=','.join(map(str, dflt['deploy_fractions'])))
    allow_daily = st.checkbox('Allow dip buys on any trading day', value=bool(dflt['allow_daily_dip_buys']))

    st.header('Costs')
    tcost_bps = st.number_input('Transaction cost (bps per buy)', min_value=0.0, value=float(dflt['transaction_cost_bps']), step=1.0)
    cash_rate = st.number_input('Cash bucket annual return (%)', min_value=0.0, value=float(dflt['cash_rate_annual'] * 100.0), step=0.25) / 100.0


def parse_float_list(s: str) -> list[float]:
    return [float(x.strip()) for x in str(s).split(',') if x.strip()]


st.subheader('Dashboard')

if not source_id:
    st.info('Open Data Manager → upload CSV into cache, then come back here.')
    st.stop()

prices_df = cache.load_prices(index_id, series_type, source_id)
if prices_df.empty:
    st.warning('Cached data is empty. Please re-upload in Data Manager.')
    st.stop()

prices_series = normalize_price_series(prices_df, 'date', 'close')
amount_per_contrib = scale_amount_for_schedule(monthly_amount, schedule)
thresholds = parse_float_list(thresholds_str)
deploy = parse_float_list(deploy_str)

if len(thresholds) != len(deploy):
    st.error('Thresholds and deploy fractions must have the same length.')
    st.stop()

summary, ledger = run_backtest(
    prices=prices_series,
    schedule=schedule,
    amount_per_contrib=amount_per_contrib,
    lookback_days=int(lookback),
    base_fraction=float(base_fraction),
    thresholds_pct=thresholds,
    deploy_fractions=deploy,
    allow_daily_dip_buys=bool(allow_daily),
    transaction_cost_bps=float(tcost_bps),
    cash_rate_annual=float(cash_rate),
)

sum_dict = summary.__dict__

col1, col2, col3, col4 = st.columns(4)
col1.metric('Total contributed', f"₹{sum_dict['total_contributed']:,.0f}")
col2.metric('Final value (Standard SIP)', f"₹{sum_dict['sip_final']:,.0f}")
col3.metric('Final value (Dip-SIP)', f"₹{sum_dict['dip_final']:,.0f}")
col4.metric('Alpha XIRR', f"{sum_dict['alpha_xirr'] * 100:,.2f}%")

col5, col6, col7, col8 = st.columns(4)
col5.metric('XIRR (Standard SIP)', f"{sum_dict['sip_xirr'] * 100:,.2f}%")
col6.metric('XIRR (Dip-SIP)', f"{sum_dict['dip_xirr'] * 100:,.2f}%")
col7.metric('Trades (SIP)', str(sum_dict['sip_trades']))
col8.metric('Trades (Dip-SIP)', str(sum_dict['dip_trades']))

st.subheader('Latest trigger')
last = ledger.iloc[-1]
A, B, C, D = st.columns(4)
A.metric('Date', str(last['date']))
B.metric('Drawdown', f"{float(last['drawdown_pct']):,.2f}%")
C.metric('Cash bucket', f"₹{float(last['dip_cash']):,.0f}")
D.metric('Suggested buy today', f"₹{float(last['dip_base_buy'] + last['dip_trigger_buy']):,.0f}")

st.subheader('Value over time')
chart_df = ledger.copy()
chart_df['date'] = pd.to_datetime(chart_df['date'])
chart_df = chart_df.set_index('date')[['sip_value', 'dip_value', 'dip_cash']]
st.line_chart(chart_df)

st.subheader('Ledger (last 250 rows)')
st.dataframe(ledger.tail(250), use_container_width=True)

st.download_button(
    'Download full ledger CSV',
    data=ledger.to_csv(index=False).encode('utf-8'),
    file_name=f'ledger_{index_id}.csv',
    mime='text/csv',
)

st.subheader('Save run to cache + export')
if st.button('Save this run'):
    plan = {
        'plan_mode': plan_mode,
        'monthly_amount_inr': monthly_amount,
        'yearly_amount_inr': yearly_amount,
        'schedule': schedule,
        'amount_per_contrib': amount_per_contrib,
    }
    params = {
        'strategy_id': 'dip_sip_band_entry',
        'lookback_days': int(lookback),
        'base_fraction': float(base_fraction),
        'thresholds_pct': thresholds,
        'deploy_fractions': deploy,
        'allow_daily_dip_buys': bool(allow_daily),
        'transaction_cost_bps': float(tcost_bps),
        'cash_rate_annual': float(cash_rate),
    }
    run_id = cache.save_run(
        index_id=index_id,
        series_type=series_type,
        source_id=source_id,
        strategy_id='dip_sip_band_entry',
        plan=plan,
        params=params,
        summary=sum_dict,
        ledger=ledger,
    )
    ledger_path = os.path.join(EXPORTS_DIR, f'ledger_{index_id}_{run_id}.csv')
    summary_path = os.path.join(EXPORTS_DIR, f'summary_{index_id}_{run_id}.json')
    ledger.to_csv(ledger_path, index=False)
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(sum_dict, f, indent=2)
    st.success(f'✅ Saved. run_id: {run_id}')
    st.write(f'Ledger → {ledger_path}')
    st.write(f'Summary → {summary_path}')
