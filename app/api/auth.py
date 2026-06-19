"""SIWE (Sign-In with Ethereum) auth: nonce -> sign -> verify -> JWT.

Read-only product, so signing is gas-free and only proves address ownership.
- GET  /v1/auth/nonce  -> issue a short-lived nonce.
- POST /v1/auth/verify -> verify an EIP-4361 message signature, upsert the user, return a JWT.
"""

import os
import secrets
import time

import jwt
from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage.repo import ensure_user

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_JWT_SECRET = os.getenv("AUTH_JWT_SECRET", "dev-insecure-secret-change-me")
_JWT_TTL = 7 * 24 * 3600  # 7 days
_NONCE_TTL = 600  # 10 minutes
_nonces: dict[str, float] = {}  # nonce -> expiry (monotonic seconds)


def _purge_nonces() -> None:
    now = time.monotonic()
    for n, exp in list(_nonces.items()):
        if exp < now:
            _nonces.pop(n, None)


def _field(message: str, prefix: str) -> str | None:
    for line in message.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


class VerifyRequest(BaseModel):
    message: str
    signature: str


@router.get("/nonce")
async def nonce() -> dict:
    _purge_nonces()
    n = secrets.token_hex(16)
    _nonces[n] = time.monotonic() + _NONCE_TTL
    return {"nonce": n}


@router.post("/verify")
async def verify(req: VerifyRequest) -> dict:
    lines = req.message.splitlines()
    address = lines[1].strip() if len(lines) > 1 else None
    msg_nonce = _field(req.message, "Nonce:")
    if not address or not msg_nonce:
        raise HTTPException(status_code=400, detail="malformed SIWE message")
    if _nonces.pop(msg_nonce, None) is None:
        raise HTTPException(status_code=401, detail="invalid or expired nonce")
    try:
        recovered = Account.recover_message(encode_defunct(text=req.message), signature=req.signature)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="bad signature") from e
    if recovered.lower() != address.lower():
        raise HTTPException(status_code=401, detail="signature does not match address")

    await ensure_user(recovered)
    now = int(time.time())
    token = jwt.encode({"sub": recovered, "iat": now, "exp": now + _JWT_TTL}, _JWT_SECRET, algorithm="HS256")
    return {"token": token, "address": recovered}


def decode_token(token: str) -> str | None:
    """Return the address (sub) of a valid JWT, or None."""
    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=["HS256"]).get("sub")
    except Exception:
        return None
