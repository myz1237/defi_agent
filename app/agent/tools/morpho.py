"""Morpho 工具:经官方 GraphQL(blue-api.morpho.org)查询仓位与市场。"""

import httpx
from langchain_core.tools import tool

from app.agent.tools.base import ALL_CHAINS, make_spec
from app.agent.tools.registry import register
from app.chains.registry import get_chain
from app.chains.rpc import resolve_chain_or_error
from app.config import settings

_POSITIONS_QUERY = """query($address: String!, $chainId: Int!) {
  userByAddress(address: $address, chainId: $chainId) {
    address
    marketPositions {
      market { marketId loanAsset { symbol } collateralAsset { symbol } }
      state { supplyAssetsUsd borrowAssetsUsd collateralUsd }
    }
  }
}"""

_MARKET_QUERY = """query($marketId: String!, $chainId: Int!) {
  marketById(marketId: $marketId, chainId: $chainId) {
    marketId lltv
    loanAsset { symbol } collateralAsset { symbol }
    state { supplyAssetsUsd borrowAssetsUsd supplyApy borrowApy utilization }
  }
}"""


def _gql(query: str, variables: dict) -> dict:
    resp = httpx.post(
        settings.morpho_graphql_url,
        json={"query": query, "variables": variables},
        timeout=settings.http_timeout,
    )
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def _usd(x) -> str:
    return f"${(x or 0):,.0f}"


@tool
def morpho_get_positions(address: str, chain: str = "ethereum") -> str:
    """查询某地址在 Morpho 的借贷仓位(供应/借出/抵押,美元计)。

    chain: Morpho 部署的链(如 ethereum、base)。
    """
    chain_key, err = resolve_chain_or_error(chain)
    if err:
        return err
    chain_id = get_chain(chain_key).chain_id
    try:
        data = _gql(_POSITIONS_QUERY, {"address": address, "chainId": chain_id})
    except Exception as e:
        return f"Morpho 仓位查询失败:{e}"

    positions = ((data.get("userByAddress") or {}).get("marketPositions")) or []
    active = [
        p
        for p in positions
        if any((p.get("state") or {}).get(k) for k in ("supplyAssetsUsd", "borrowAssetsUsd", "collateralUsd"))
    ]
    if not active:
        return f"{address} 在 {chain_key} 的 Morpho 无活跃仓位。"

    lines = [f"{address} 在 {chain_key} 的 Morpho 仓位({len(active)} 个市场):"]
    for p in active:
        m = p.get("market") or {}
        st = p.get("state") or {}
        loan = (m.get("loanAsset") or {}).get("symbol")
        coll = (m.get("collateralAsset") or {}).get("symbol")
        lines.append(
            f"  {loan}/{coll}: 供应={_usd(st.get('supplyAssetsUsd'))} "
            f"借出={_usd(st.get('borrowAssetsUsd'))} 抵押={_usd(st.get('collateralUsd'))} "
            f"[marketId={m.get('marketId')}]"
        )
    return "\n".join(lines)


@tool
def morpho_get_market(market_id: str, chain: str = "ethereum") -> str:
    """按 marketId(0x… 市场唯一 id)查询 Morpho 市场数据(APY/LLTV/规模/利用率)。

    chain: ethereum、base 等。
    """
    chain_key, err = resolve_chain_or_error(chain)
    if err:
        return err
    chain_id = get_chain(chain_key).chain_id
    try:
        data = _gql(_MARKET_QUERY, {"marketId": market_id, "chainId": chain_id})
    except Exception as e:
        return f"Morpho 市场查询失败:{e}"

    m = data.get("marketById")
    if not m:
        return f"未找到市场 {market_id}(链 {chain_key})。"
    st = m.get("state") or {}
    loan = (m.get("loanAsset") or {}).get("symbol")
    coll = (m.get("collateralAsset") or {}).get("symbol")
    lines = [f"Morpho 市场 {loan}/{coll}(链 {chain_key}) marketId={m.get('marketId')}"]
    if m.get("lltv"):
        lines.append(f"  LLTV={int(m['lltv']) / 1e18 * 100:.1f}%")
    lines.append(f"  供应={_usd(st.get('supplyAssetsUsd'))} 借出={_usd(st.get('borrowAssetsUsd'))}")
    if st.get("supplyApy") is not None:
        lines.append(
            f"  supplyAPY={st['supplyApy'] * 100:.2f}% "
            f"borrowAPY={(st.get('borrowApy') or 0) * 100:.2f}% "
            f"利用率={(st.get('utilization') or 0) * 100:.1f}%"
        )
    return "\n".join(lines)


register(make_spec(morpho_get_positions, "morpho", ALL_CHAINS))
register(make_spec(morpho_get_market, "morpho", ALL_CHAINS))
