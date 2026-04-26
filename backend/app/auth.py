"""Authentication: username/password login with JWT sessions.

Single-user app, so credentials live in config.json (admin_username, admin_password).
On successful POST /auth/login we issue a JWT. The frontend stores it in
localStorage and sends it in the Authorization header on every request.
"""
import hmac
import json
import time
import base64
import hashlib
from typing import Optional
from fastapi import HTTPException, Header, status
from .config import settings


# ---- minimal JWT impl (HS256) so we don't need an extra dependency ----

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _sign(message: bytes, secret: str) -> bytes:
    return hmac.new(secret.encode(), message, hashlib.sha256).digest()


def issue_token(username: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + (settings.jwt_ttl_hours * 3600),
    }
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64url(_sign(f"{h}.{p}".encode(), settings.jwt_secret))
    return f"{h}.{p}.{sig}"


def verify_token(token: str) -> Optional[dict]:
    """Return the payload if valid and unexpired, else None."""
    try:
        h, p, sig = token.split(".")
    except ValueError:
        return None
    expected = _b64url(_sign(f"{h}.{p}".encode(), settings.jwt_secret))
    if not hmac.compare_digest(expected, sig):
        return None
    try:
        payload = json.loads(_b64url_decode(p))
    except (ValueError, json.JSONDecodeError):
        return None
    if payload.get("exp", 0) < int(time.time()):
        return None
    return payload


def authenticate(username: str, password: str) -> bool:
    """Compare against the admin credentials in config. Constant-time."""
    u_ok = hmac.compare_digest(username.encode(), settings.admin_username.encode())
    p_ok = hmac.compare_digest(password.encode(), settings.admin_password.encode())
    return u_ok and p_ok


# ---- FastAPI dependency ----

def require_auth(authorization: str = Header(default="")) -> str:
    """Verify the Authorization: Bearer <token> header. Returns the username."""
    if settings.admin_password == "change-me-before-deploying":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "admin password not configured")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    token = authorization[7:].strip()
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token")
    return payload["sub"]
