"""SIWE auth: sign with a known keypair, verify recovers the address and issues a usable JWT."""

import asyncio

import pytest
from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import HTTPException

import app.api.auth as auth


def _siwe_message(address: str, nonce: str) -> str:
    return (
        "example.com wants you to sign in with your Ethereum account:\n"
        f"{address}\n\nSign in to DeFi Agent.\n\n"
        f"URI: https://example.com\nVersion: 1\nChain ID: 1\nNonce: {nonce}\nIssued At: 2026-01-01T00:00:00Z"
    )


def _sig(acct, message: str) -> str:
    raw = acct.sign_message(encode_defunct(text=message)).signature
    sig = raw.hex()
    return sig if sig.startswith("0x") else "0x" + sig


def test_siwe_roundtrip(monkeypatch):
    async def _noop(_addr):
        return None

    monkeypatch.setattr(auth, "ensure_user", _noop)
    acct = Account.from_key("0x" + "1" * 64)

    async def run():
        nonce = (await auth.nonce())["nonce"]
        msg = _siwe_message(acct.address, nonce)
        return await auth.verify(auth.VerifyRequest(message=msg, signature=_sig(acct, msg)))

    res = asyncio.run(run())
    assert res["address"].lower() == acct.address.lower()
    assert auth.decode_token(res["token"]).lower() == acct.address.lower()


def test_siwe_bad_signature(monkeypatch):
    async def _noop(_addr):
        return None

    monkeypatch.setattr(auth, "ensure_user", _noop)
    acct = Account.from_key("0x" + "2" * 64)

    async def run():
        nonce = (await auth.nonce())["nonce"]
        msg = _siwe_message(acct.address, nonce)
        # Signature over a different message must not verify.
        return await auth.verify(auth.VerifyRequest(message=msg, signature=_sig(acct, "tampered")))

    with pytest.raises(HTTPException):
        asyncio.run(run())


def test_invalid_token():
    assert auth.decode_token("not-a-jwt") is None
