"""Supported EVM chain registry. Source of truth for the supported scope.

Adding a chain = one row in `_DEFAULTS` + one override name in `_ENV_KEYS`.
Defaults use public RPC (publicnode); override to a private node via the matching env var.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Chain:
    key: str  # canonical key: ethereum/bsc/arbitrum/base/optimism
    name: str  # display name
    chain_id: int
    rpc_url: str


# key -> (display name, chainId, default public RPC)
_DEFAULTS: dict[str, tuple[str, int, str]] = {
    "ethereum": ("Ethereum", 1, "https://ethereum-rpc.publicnode.com"),
    "bsc": ("BNB Smart Chain", 56, "https://bsc-rpc.publicnode.com"),
    "arbitrum": ("Arbitrum One", 42161, "https://arbitrum-one-rpc.publicnode.com"),
    "base": ("Base", 8453, "https://base-rpc.publicnode.com"),
    "optimism": ("OP Mainnet", 10, "https://optimism-rpc.publicnode.com"),
}

# Environment variable names for overrides (set when using a private RPC)
_ENV_KEYS: dict[str, str] = {
    "ethereum": "ETH_RPC_URL",
    "bsc": "BNB_RPC_URL",
    "arbitrum": "ARB_RPC_URL",
    "base": "BASE_RPC_URL",
    "optimism": "OPT_RPC_URL",
}

# Aliases users might type -> canonical key
_ALIASES: dict[str, str] = {
    "eth": "ethereum",
    "mainnet": "ethereum",
    "ethereum-mainnet": "ethereum",
    "bnb": "bsc",
    "binance": "bsc",
    "bnb-chain": "bsc",
    "arb": "arbitrum",
    "arbitrum-one": "arbitrum",
    "op": "optimism",
    "opt": "optimism",
    "op-mainnet": "optimism",
}

DEFAULT_CHAIN = "ethereum"


def _build() -> dict[str, Chain]:
    chains: dict[str, Chain] = {}
    for key, (name, chain_id, default_rpc) in _DEFAULTS.items():
        rpc = os.getenv(_ENV_KEYS[key], default_rpc)
        chains[key] = Chain(key=key, name=name, chain_id=chain_id, rpc_url=rpc)
    return chains


CHAINS: dict[str, Chain] = _build()

# ENS resolution always uses mainnet (simple version: no ENSIP-11 multi-chain records)
ENS_RPC_URL: str = os.getenv("ENS_RPC_URL", CHAINS["ethereum"].rpc_url)


def supported_keys() -> tuple[str, ...]:
    return tuple(CHAINS.keys())


def normalize_chain(key: str | None) -> str:
    """Normalize aliases/casing to the canonical key; empty values fall back to the default chain."""
    if not key:
        return DEFAULT_CHAIN
    k = key.strip().lower()
    return _ALIASES.get(k, k)


def get_chain(key: str | None) -> Chain | None:
    """Get the chain config; returns None if unsupported (for constraint/refusal checks)."""
    return CHAINS.get(normalize_chain(key))


def chain_id_to_key(chain_id: int) -> str | None:
    for c in CHAINS.values():
        if c.chain_id == chain_id:
            return c.key
    return None
