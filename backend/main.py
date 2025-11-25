# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import httpx
from app.models.session_store import save_user, get_user
from app.services.zoho_service import build_auth_url, exchange_code_for_token, refresh_access_token, fetch_employee_form

load_dotenv()

app = FastAPI()
STREAMLIT_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501")
OAUTH_BASE = os.getenv("OAUTH_BASE")

# ---------------------- CORS ----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------------------- LOGIN ----------------------
from typing import Optional

DEFAULT_EMAIL = "kartik.lala@prodevans.com"

@app.get("/auth/zoho/login")
async def login(email: Optional[str] = None):
    """
    Login endpoint.
    If email is provided and user exists in DB, attempts silent login.
    Otherwise redirects to Zoho OAuth consent.
    """
    if email:
        user = await get_user(email)
        if user:
            access = await refresh_access_token(email)
            if access:
                # Silent login successful
                return {"status": "ok", "email": email, "message": "Already logged in"}

    # No user or token invalid → redirect to Zoho consent
    auth_url = build_auth_url()
    return RedirectResponse(auth_url)


# ---------------------- CALLBACK ----------------------
@app.get("/auth/zoho/callback")
async def callback(code: str):
    """
    Exchange code for tokens, fetch user info, fetch Zoho People employee form,
    save everything in MongoDB, and redirect to Streamlit frontend.
    """
    # 1️⃣ Exchange code for token
    token_data = await exchange_code_for_token(code)
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)
    api_domain = token_data.get("api_domain", "https://people.zoho.in")

    # 2️⃣ Fetch basic user info
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{OAUTH_BASE}/oauth/user/info",
            headers={"Authorization": f"Zoho-oauthtoken {access_token}"}
        )
        resp.raise_for_status()
        user_info = resp.json()

    email = user_info.get("Email") or os.getenv("DEFAULT_EMAIL", "jack@gmail.com")

    # 2️⃣.1 Fetch detailed employee info from Zoho People form
    employee_form_data_full = await fetch_employee_form(access_token, email)
    if employee_form_data_full and isinstance(employee_form_data_full, list) and len(employee_form_data_full) > 0:
        record = employee_form_data_full[0]
        employee_form_data = {
            "First Name": record.get("First Name"),
            "First Name": record.get("First Name"),
            "Department": record.get("Department"),
            "recordId": record.get("recordId"),
            "Manager": record.get("Reporting To"),
            "Designation ": record.get("Designation"),
            "Production Status": record.get("Production Status"),
            "EmployeeID": record.get("EmployeeID"),
            "Pmail": record.get("EmployeeID"),
            "Mobile Phone": record.get("Mobile Phone"),
            # add any other fields you want
        }
    else:
        employee_form_data = {}        

    # 3️⃣ Save/update in MongoDB (merge both user_info + employee_form_data)
    await save_user(
        email=email,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        api_domain=api_domain,
        user_info={
            "basic_info": user_info,
            "employee_form": employee_form_data
        }
    )

    # 4️⃣ Redirect to Streamlit frontend
    return RedirectResponse(f"{STREAMLIT_URL}?email={email}")
# ---------------------- TEST ----------------------
@app.get("/")
async def root():
    return {"msg": "Backend Running"}
