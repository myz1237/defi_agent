"""按链获取 web3 客户端(同步 HTTPProvider,带缓存)。"""

from functools import cache, lru_cache

from web3 import Web3

from app.chains.registry import ENS_RPC_URL, get_chain, normalize_chain, supported_keys
from app.config import settings


@cache
def get_web3(chain_key: str) -> Web3:
    chain = get_chain(chain_key)
    if chain is None:
        raise ValueError(f"不支持的链 {chain_key!r};支持:{', '.join(supported_keys())}")
    return Web3(Web3.HTTPProvider(chain.rpc_url, request_kwargs={"timeout": settings.http_timeout}))


@lru_cache(maxsize=1)
def get_ens_web3() -> Web3:
    """ENS 解析固定走主网端点。"""
    return Web3(Web3.HTTPProvider(ENS_RPC_URL, request_kwargs={"timeout": settings.http_timeout}))


def resolve_chain_or_error(chain: str | None) -> tuple[str | None, str | None]:
    """规范化链键;不支持时返回 (None, 错误信息)。"""
    key = normalize_chain(chain)
    if get_chain(key) is None:
        return None, f"不支持的链:{chain}。支持:{', '.join(supported_keys())}"
    return key, None
