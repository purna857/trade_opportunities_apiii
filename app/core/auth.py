from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import Header, HTTPException, Request, status

from app.config import get_settings


@dataclass
class AuthContext:
    user_type: str
    session_id: str
    api_key_authenticated: bool


async def get_auth_context(
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> AuthContext:
    settings = get_settings()

    session_id = request.session.get("session_id")
    if not session_id:
        session_id = str(uuid4())
        request.session["session_id"] = session_id

    provided_api_key = x_api_key
    if provided_api_key and provided_api_key == settings.api_key:
        request.session["auth_mode"] = "api_key"
        return AuthContext(user_type="api_key", session_id=session_id, api_key_authenticated=True)

    if settings.guest_access_enabled:
        request.session.setdefault("guest_id", f"guest-{uuid4()}")
        request.session["auth_mode"] = "guest"
        return AuthContext(user_type="guest", session_id=session_id, api_key_authenticated=False)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid API key",
        headers={"WWW-Authenticate": "API-Key"},
    )
