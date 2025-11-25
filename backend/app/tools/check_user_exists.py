from langchain.tools import tool
from app.models.session_store import session_store
from app.utils.logger import get_logger

logger = get_logger()

@tool("check_user_exists")
async def check_user_exists(email: str):
    """
    Check if a user exists in MongoDB using email.
    Returns True if exists, else False.
    """
    logger.info(f"Checking if user exists: {email}")
    user = await session_store.get_user_by_email(email)
    return user is not None
