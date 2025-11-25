# streamlit_app.py
import streamlit as st
import requests
import os

# ------------------------------
# Config
# ------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8002")

# ------------------------------
# Helper functions
# ------------------------------
def get_query_param(key: str, default=None):
    query_params = st.experimental_get_query_params()
    return query_params.get(key, [default])[0]

def check_user_logged_in(email):
    """Check if user exists and has a valid token."""
    try:
        resp = requests.get(f"{BACKEND_URL}/auth/zoho/login", params={"email": email}, allow_redirects=False)
        if resp.status_code in [302, 307]:  # Redirect → consent needed
            return False, resp.headers.get("location")
        return True, None
    except Exception as e:
        st.error(f"Error checking login: {e}")
        return False, None

# ------------------------------
# Main
# ------------------------------
st.title("Zoho Auto Login Demo")

# 1️⃣ Read email from query param (or default)
email = get_query_param("email", "kartik.lala@prodevans.com")

# 2️⃣ Initialize session state
if "login_checked" not in st.session_state:
    st.session_state.login_checked = False
    st.session_state.redirect_url = None

# 3️⃣ Only check login once
if not st.session_state.login_checked:
    logged_in, redirect_url = check_user_logged_in(email)
    st.session_state.login_checked = True
    st.session_state.redirect_url = redirect_url
else:
    logged_in = st.session_state.redirect_url is None
    redirect_url = st.session_state.redirect_url

# 4️⃣ Handle login state
if logged_in:
    st.success(f"Welcome back, {email}!")
    st.info("You are already logged in. No need for Zoho consent again.")
else:
    st.warning("You are not logged in or token expired.")
    st.write(f"Redirecting to Zoho consent for {email}...")
    if redirect_url:
        st.markdown(f'<meta http-equiv="refresh" content="0; url={redirect_url}" />', unsafe_allow_html=True)

# ------------------------------
# Example: show user info if logged in
# ------------------------------
if "logged_in" not in st.session_state:
    # First check
    resp = requests.get(f"{BACKEND_URL}/auth/zoho/login", params={"email": email}, allow_redirects=False)
    if resp.status_code == 200:
        st.session_state.logged_in = True
    elif resp.status_code in [307, 302]:
        # Redirect to Zoho consent
        st.session_state.logged_in = False
        redirect_url = resp.headers.get("location")
        st.markdown(f'<meta http-equiv="refresh" content="0; url={redirect_url}" />', unsafe_allow_html=True)

