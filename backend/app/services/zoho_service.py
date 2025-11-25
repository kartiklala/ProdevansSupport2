# zoho_service.py
import httpx
from dotenv import load_dotenv
import os
from app.models.session_store import get_user, update_access_token
import time

load_dotenv()

ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI")
OAUTH_BASE = os.getenv("OAUTH_BASE")


def build_auth_url():
    scopes = ",".join([
        "ZohoPeople.employee.READ",
        "ZohoPeople.leave.ALL",
        "ZohoPeople.attendance.READ",
        "ZohoPeople.forms.ALL",
        "AaaServer.profile.READ"
    ])
    return (
        f"{OAUTH_BASE}/oauth/v2/auth?"
        f"scope={scopes}&response_type=code&access_type=offline&"
        f"client_id={ZOHO_CLIENT_ID}&redirect_uri={ZOHO_REDIRECT_URI}&prompt=consent"
    )


async def exchange_code_for_token(code: str):
    url = f"{OAUTH_BASE}/oauth/v2/token"
    params = {
        "grant_type": "authorization_code",
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "redirect_uri": ZOHO_REDIRECT_URI,
        "code": code
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params=params)
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(email):
    user = await get_user(email)
    if not user:
        return None

    # If still valid, return
    if user["expires_at"] > int(time.time()):
        return user["access_token"]

    # Refresh token flow
    url = f"{OAUTH_BASE}/oauth/v2/token"
    params = {
        "grant_type": "refresh_token",
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "refresh_token": user["refresh_token"]
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    await update_access_token(email, data["access_token"], data.get("expires_in", 3600))
    return data["access_token"]

PEOPLE_API_BASE = "https://people.zoho.in/people/api/forms/P_EmployeeView/records"

async def fetch_employee_form(access_token, email):
    """
    Fetch detailed employee info from Zoho People form based on email
    """
    params = {
        "searchColumn": "EMPLOYEEMAILALIAS",
        "searchValue": email
    }
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(PEOPLE_API_BASE, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()
