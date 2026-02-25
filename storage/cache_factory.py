from __future__ import annotations

import os
import streamlit as st


def get_cache(db_path: str = './data/cache.sqlite'):
    """Factory: returns SupabaseCache if SUPABASE_URL exists in secrets, else LocalCache.
    
    This allows:
    - Local development: uses SQLite (fast, no internet)
    - Online Streamlit Cloud: uses Supabase (persistent, shared)
    """
    
    # Check if running on Streamlit Cloud with Supabase configured
    if 'SUPABASE_URL' in st.secrets and 'SUPABASE_KEY' in st.secrets:
        from storage.supabase_cache import SupabaseCache
        return SupabaseCache(
            supabase_url=st.secrets['SUPABASE_URL'],
            supabase_key=st.secrets['SUPABASE_KEY'],
        )
    
    # Fall back to local SQLite
    from storage.cache import LocalCache
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return LocalCache(db_path)
