
import streamlit as st
import yaml
import streamlit_authenticator as stauth

# Load credentials
with open("config/credentials.yaml", "r") as f:
    cfg = yaml.safe_load(f)

authenticator = stauth.Authenticate(
    cfg["credentials"],
    cfg["cookie"]["name"],
    cfg["cookie"]["key"],
    cfg["cookie"]["expiry_days"]
)

# Simple main page login
name, authentication_status, username = authenticator.login(location="main")

if authentication_status == False:
    st.error("❌ Username/password is incorrect")
elif authentication_status is None:
    st.title("🔐 Login Required")
else:
    st.success(f"✅ Welcome {name}!")
    st.info(f"Username: {username}")
    st.sidebar.success(f"Logged in as {name}")
    authenticator.logout("Logout", "sidebar")
