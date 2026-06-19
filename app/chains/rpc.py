"""Get a web3 client per chain (synchronous HTTPProvider, cached)."""

from functools import cache, lru_cache

from web3 import Web3

from app.chains.registry import ENS_RPC_URL, get_chain, normalize_chain, supported_keys
from app.config import settings


@cache
def get_web3(chain_key: str) -> Web3:
    chain = get_chain(chain_key)
    if chain is None:
        raise ValueError(f"Unsupported chain {chain_key!r}; supported: {', '.join(supported_keys())}")
    return Web3(Web3.HTTPProvider(chain.rpc_url, request_kwargs={"timeout": settings.http_timeout}))


@lru_cache(maxsize=1)
def get_ens_web3() -> Web3:
    """ENS resolution always uses the mainnet endpoint."""
    return Web3(Web3.HTTPProvider(ENS_RPC_URL, request_kwargs={"timeout": settings.http_timeout}))


def resolve_chain_or_error(chain: str | None) -> tuple[str | None, str | None]:
    """Normalize the chain key; return (None, error message) if unsupported."""
    key = normalize_chain(chain)
    if get_chain(key) is None:
        return None, f"Unsupported chain: {chain}. Supported: {', '.join(supported_keys())}"
    return key, None
