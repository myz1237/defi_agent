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
    if x_api_key and x_api_key in _widget_keys():
        return Identity(kind="widget", user_id=f"widget:{x_api_key[:8]}", session_id=x_api_key[:8])

    if authorization and authorization.lower().startswith("bearer "):
        # TODO(M8): validate the SIWE-issued JWT; for now take the token tail as a placeholder user_id
        token = authorization.split(" ", 1)[1]
        return Identity(kind="siwe", user_id=f"siwe:{token[-12:]}", session_id=token[-12:])

    session_id = x_session_id or f"anon-{uuid.uuid4().hex[:16]}"
    return Identity(kind="anon", user_id=f"anon:{session_id}", session_id=session_id)
