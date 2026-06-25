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
      healthFactor
      market {
        marketId lltv
        loanAsset { symbol decimals }
        collateralAsset { symbol decimals }
      }
      state { collateral collateralUsd borrowAssets borrowAssetsUsd supplyAssetsUsd }
    }
    vaultPositions {
      vault { name asset { symbol decimals } state { netApy } }
      state { assets assetsUsd }
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


def _usd_compact(value) -> str:
    v = float(value or 0)
    a = abs(v)
    if a >= 1e9:
        return f"${v / 1e9:.1f}B"
    if a >= 1e6:
        return f"${v / 1e6:.1f}M"
    if a >= 1e3:
        return f"${v / 1e3:.1f}K"
    return f"${v:,.0f}"


def _fmt_token(raw, decimals) -> str:
    try:
        v = int(raw) / (10 ** int(decimals or 0))
    except Exception:
        return str(raw)
    s = f"{v:,.4f}".rstrip("0").rstrip(".")
    return s or "0"


def _build_view(address: str, chain_key: str, user: dict) -> dict:
    """Shape the Morpho user data into the frontend MorphoView card props."""
    chain_name = get_chain(chain_key).name
    net = 0.0
    borrow_markets = []
    for p in user.get("marketPositions") or []:
        m = p.get("market") or {}
        st = p.get("state") or {}
        loan = m.get("loanAsset") or {}
        coll = m.get("collateralAsset") or {}
        coll_usd = float(st.get("collateralUsd") or 0)
        borrow_usd = float(st.get("borrowAssetsUsd") or 0)
        net += coll_usd - borrow_usd + float(st.get("supplyAssetsUsd") or 0)
        if not (coll_usd or borrow_usd):
            continue
        hf = p.get("healthFactor")
        borrow_markets.append(
            {
                "collateralSymbol": coll.get("symbol") or "—",
                "loanSymbol": loan.get("symbol") or "—",
                "chainName": chain_name,
                "healthFactor": f"{float(hf):.2f}" if hf is not None else "—",
                "collateralAmount": (
                    f"{_fmt_token(st.get('collateral'), coll.get('decimals'))} {coll.get('symbol') or ''}".strip()
                ),
                "borrowAmount": (
                    f"{_fmt_token(st.get('borrowAssets'), loan.get('decimals'))} {loan.get('symbol') or ''}".strip()
                ),
                "ltvPct": round(borrow_usd / coll_usd * 100, 1) if coll_usd else 0,
                "lltvPct": round(int(m["lltv"]) / 1e18 * 100, 1) if m.get("lltv") else 0,
            }
        )

    vaults = []
    for vp in user.get("vaultPositions") or []:
        vs = vp.get("state") or {}
        if not float(vs.get("assetsUsd") or 0):
            continue
        v = vp.get("vault") or {}
        asset = v.get("asset") or {}
        net += float(vs.get("assetsUsd") or 0)
        net_apy = (v.get("state") or {}).get("netApy") or 0
        deposit = f"{_fmt_token(vs.get('assets'), asset.get('decimals'))} {asset.get('symbol') or ''} deposited"
        vaults.append(
            {
                "name": v.get("name") or "Vault",
                "depositLabel": deposit.strip(),
                "apyLabel": f"{float(net_apy) * 100:.2f}%",
            }
        )

    return {
        "address": f"{address[:6]}…{address[-4:]}",
        "netWorthLabel": _usd_compact(net),
        "borrowMarkets": borrow_markets,
        "vaults": vaults,
    }


@tool(response_format="content_and_artifact")
def morpho_get_positions(address: str, chain: str = "ethereum") -> tuple[str, dict | None]:
    """Query an address's Morpho lending positions (supply/borrow/collateral, in USD).

    chain: a chain where Morpho is deployed (e.g. ethereum, base).
    """
    chain_key, err = resolve_chain_or_error(chain)
    if err:
        return err, None
    chain_id = get_chain(chain_key).chain_id
    try:
        data = _gql(_POSITIONS_QUERY, {"address": address, "chainId": chain_id})
    except Exception as e:
        return f"Morpho positions query failed: {e}", None

    user = data.get("userByAddress") or {}
    positions = user.get("marketPositions") or []
    active = [
        p
        for p in positions
        if any((p.get("state") or {}).get(k) for k in ("supplyAssetsUsd", "borrowAssetsUsd", "collateralUsd"))
    ]
    has_vaults = any(float((vp.get("state") or {}).get("assetsUsd") or 0) for vp in (user.get("vaultPositions") or []))
    if not active and not has_vaults:
        return f"{address} has no active Morpho positions on {chain_key}.", None

    # LLM-facing summary (concise; the UI renders the full card).
    lines = [f"{address} Morpho positions on {chain_key} ({len(active)} markets):"]
    for p in active:
        m = p.get("market") or {}
        st = p.get("state") or {}
        loan = (m.get("loanAsset") or {}).get("symbol")
        coll = (m.get("collateralAsset") or {}).get("symbol")
        lines.append(
            f"  {loan}/{coll}: borrow={_usd(st.get('borrowAssetsUsd'))} "
            f"collateral={_usd(st.get('collateralUsd'))} healthFactor={p.get('healthFactor')}"
        )
    return "\n".join(lines), {"kind": "morpho", "data": _build_view(address, chain_key, user)}


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
