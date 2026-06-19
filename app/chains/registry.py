"""受支持 EVM 链注册表。支持范围的真值来源。

加新链 = 在 `_DEFAULTS` 增一行 + `_ENV_KEYS` 一个覆盖名即可。
默认用公共 RPC(publicnode),可用对应 env 覆盖为私有节点。
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Chain:
    key: str  # 规范键:ethereum/bsc/arbitrum/base/optimism
    name: str  # 展示名
    chain_id: int
    rpc_url: str


# key -> (展示名, chainId, 默认公共 RPC)
_DEFAULTS: dict[str, tuple[str, int, str]] = {
    "ethereum": ("Ethereum", 1, "https://ethereum-rpc.publicnode.com"),
    "bsc": ("BNB Smart Chain", 56, "https://bsc-rpc.publicnode.com"),
    "arbitrum": ("Arbitrum One", 42161, "https://arbitrum-one-rpc.publicnode.com"),
    "base": ("Base", 8453, "https://base-rpc.publicnode.com"),
    "optimism": ("OP Mainnet", 10, "https://optimism-rpc.publicnode.com"),
}

# 覆盖用的环境变量名(私有 RPC 时设置)
_ENV_KEYS: dict[str, str] = {
    "ethereum": "ETH_RPC_URL",
    "bsc": "BNB_RPC_URL",
    "arbitrum": "ARB_RPC_URL",
    "base": "BASE_RPC_URL",
    "optimism": "OPT_RPC_URL",
}

# 用户可能用的别名 -> 规范键
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

# ENS 解析固定走主网(简单版:不做 ENSIP-11 多链记录)
ENS_RPC_URL: str = os.getenv("ENS_RPC_URL", CHAINS["ethereum"].rpc_url)


def supported_keys() -> tuple[str, ...]:
    return tuple(CHAINS.keys())


def normalize_chain(key: str | None) -> str:
    """把别名/大小写规范化为标准键;空值回落默认链。"""
    if not key:
        return DEFAULT_CHAIN
    k = key.strip().lower()
    return _ALIASES.get(k, k)


def get_chain(key: str | None) -> Chain | None:
    """取链配置;不支持返回 None(供约束/拒绝判断)。"""
    return CHAINS.get(normalize_chain(key))


def chain_id_to_key(chain_id: int) -> str | None:
    for c in CHAINS.values():
        if c.chain_id == chain_id:
            return c.key
    return None
