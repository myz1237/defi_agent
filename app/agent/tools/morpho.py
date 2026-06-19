"""Morpho tools: query positions and markets via the official GraphQL (blue-api.morpho.org)."""

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
    """Query an address's Morpho lending positions (supply/borrow/collateral, in USD).

    chain: a chain where Morpho is deployed (e.g. ethereum, base).
    """
    chain_key, err = resolve_chain_or_error(chain)
    if err:
        return err
    chain_id = get_chain(chain_key).chain_id
    try:
        data = _gql(_POSITIONS_QUERY, {"address": address, "chainId": chain_id})
    except Exception as e:
        return f"Morpho positions query failed: {e}"

    positions = ((data.get("userByAddress") or {}).get("marketPositions")) or []
    active = [
        p
        for p in positions
        if any((p.get("state") or {}).get(k) for k in ("supplyAssetsUsd", "borrowAssetsUsd", "collateralUsd"))
    ]
    if not active:
        return f"{address} has no active Morpho positions on {chain_key}."

    lines = [f"{address} Morpho positions on {chain_key} ({len(active)} markets):"]
    for p in active:
        m = p.get("market") or {}
        st = p.get("state") or {}
        loan = (m.get("loanAsset") or {}).get("symbol")
        coll = (m.get("collateralAsset") or {}).get("symbol")
        lines.append(
            f"  {loan}/{coll}: supply={_usd(st.get('supplyAssetsUsd'))} "
            f"borrow={_usd(st.get('borrowAssetsUsd'))} collateral={_usd(st.get('collateralUsd'))} "
            f"[marketId={m.get('marketId')}]"
        )
    return "\n".join(lines)


@tool
def morpho_get_market(market_id: str, chain: str = "ethereum") -> str:
    """Query Morpho market data by marketId (the 0x... unique market id): APY/LLTV/size/utilization.

    chain: ethereum, base, etc.
    """
    chain_key, err = resolve_chain_or_error(chain)
    if err:
        return err
    chain_id = get_chain(chain_key).chain_id
    try:
        data = _gql(_MARKET_QUERY, {"marketId": market_id, "chainId": chain_id})
    except Exception as e:
        return f"Morpho market query failed: {e}"

    m = data.get("marketById")
    if not m:
        return f"Market {market_id} not found (chain {chain_key})."
    st = m.get("state") or {}
    loan = (m.get("loanAsset") or {}).get("symbol")
    coll = (m.get("collateralAsset") or {}).get("symbol")
    lines = [f"Morpho market {loan}/{coll} (chain {chain_key}) marketId={m.get('marketId')}"]
    if m.get("lltv"):
        lines.append(f"  LLTV={int(m['lltv']) / 1e18 * 100:.1f}%")
    lines.append(f"  supply={_usd(st.get('supplyAssetsUsd'))} borrow={_usd(st.get('borrowAssetsUsd'))}")
    if st.get("supplyApy") is not None:
        lines.append(
            f"  supplyAPY={st['supplyApy'] * 100:.2f}% "
            f"borrowAPY={(st.get('borrowApy') or 0) * 100:.2f}% "
            f"utilization={(st.get('utilization') or 0) * 100:.1f}%"
        )
    return "\n".join(lines)


register(make_spec(morpho_get_positions, "morpho", ALL_CHAINS))
register(make_spec(morpho_get_market, "morpho", ALL_CHAINS))
