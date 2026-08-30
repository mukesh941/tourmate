"""
Shared FastAPI dependencies: extract + validate the bearer token, load the current user.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.services.auth_service import AuthError, get_current_user

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token.")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise ValueError("Not an access token.")
        return await get_current_user(payload["sub"])
    except (ValueError, AuthError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc


async def require_admin(user=Depends(get_current_user_dependency)):
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required.")
    return user
