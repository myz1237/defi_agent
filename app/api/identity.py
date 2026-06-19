"""Three-way identity dependency: widget (API key) / SIWE (JWT) / anonymous session.

Minimal viable version:
- X-API-Key matching WIDGET_API_KEYS (comma-separated env) -> widget identity.
- Authorization: Bearer <jwt> -> siwe identity (full SIWE signature verification deferred to M8 frontend
  integration; here we only take sub).
- Otherwise anonymous: derive a stable user_id from X-Session-Id (newly generated if absent).
Rate-limit tiers can be implemented per identity.kind (later).
"""

import os
import uuid
from dataclasses import dataclass

from fastapi import Header, Request

from app.api.auth import decode_token
from app.storage.repo import is_valid_api_key


@dataclass(frozen=True)
class Identity:
    kind: str  # widget | siwe | anon
    user_id: str
    session_id: str


def _widget_keys() -> set[str]:
    raw = os.getenv("WIDGET_API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


async def get_identity(
    request: Request,
    x_api_key: str | None = Header(default=None),
    x_session_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> Identity:
    # Widget key: env allowlist first (no DB round-trip), then the api_keys table.
    if x_api_key and (x_api_key in _widget_keys() or await is_valid_api_key(x_api_key)):
        return Identity(kind="widget", user_id=f"widget:{x_api_key[:8]}", session_id=x_api_key[:8])

    if authorization and authorization.lower().startswith("bearer "):
        address = decode_token(authorization.split(" ", 1)[1])
        if address:
            return Identity(kind="siwe", user_id=f"siwe:{address.lower()}", session_id=address.lower())
        # Invalid/expired token: fall through to an anonymous session.

    session_id = x_session_id or f"anon-{uuid.uuid4().hex[:16]}"
    return Identity(kind="anon", user_id=f"anon:{session_id}", session_id=session_id)
