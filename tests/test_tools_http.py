"""HTTP-based tools (LI.FI, Morpho) with respx-mocked responses."""

import httpx
import respx

from app.agent.tools.lifi import lifi_get_status
from app.agent.tools.morpho import morpho_get_market, morpho_get_positions


@respx.mock
def test_lifi_status_done():
    respx.get("https://li.quest/v1/status").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "DONE",
                "substatus": "COMPLETED",
                "tool": "squid",
                "sending": {"chainId": 1, "txHash": "0xabc", "token": {"symbol": "USDT"}, "amount": "100"},
                "receiving": {"chainId": 56, "txHash": "0xdef", "token": {"symbol": "BNB"}, "amount": "200"},
            },
        )
    )
    out = lifi_get_status.invoke({"tx_hash": "0xabc"})
    assert "DONE" in out
    assert "squid" in out
    assert "USDT" in out
    assert "BNB" in out


@respx.mock
def test_morpho_positions_active():
    respx.post("https://blue-api.morpho.org/graphql").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "userByAddress": {
                        "address": "0x1",
                        "marketPositions": [
                            {
                                "market": {
                                    "marketId": "0xm",
                                    "loanAsset": {"symbol": "RLUSD"},
                                    "collateralAsset": {"symbol": "cbBTC"},
                                },
                                "state": {"supplyAssetsUsd": 0, "borrowAssetsUsd": 1000.0, "collateralUsd": 2000.0},
                            }
                        ],
                    }
                }
            },
        )
    )
    out = morpho_get_positions.invoke({"address": "0x1"})
    assert "RLUSD/cbBTC" in out
    assert "1,000" in out


@respx.mock
def test_morpho_positions_empty():
    respx.post("https://blue-api.morpho.org/graphql").mock(
        return_value=httpx.Response(200, json={"data": {"userByAddress": {"address": "0x1", "marketPositions": []}}})
    )
    out = morpho_get_positions.invoke({"address": "0x1"})
    assert "no active Morpho positions" in out


@respx.mock
def test_morpho_market():
    respx.post("https://blue-api.morpho.org/graphql").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "marketById": {
                        "marketId": "0xm",
                        "lltv": "860000000000000000",
                        "loanAsset": {"symbol": "RLUSD"},
                        "collateralAsset": {"symbol": "cbBTC"},
                        "state": {
                            "supplyAssetsUsd": 1000,
                            "borrowAssetsUsd": 900,
                            "supplyApy": 0.0289,
                            "borrowApy": 0.0321,
                            "utilization": 0.9,
                        },
                    }
                }
            },
        )
    )
    out = morpho_get_market.invoke({"market_id": "0xm"})
    assert "RLUSD/cbBTC" in out
    assert "LLTV=86.0%" in out
    assert "borrowAPY=3.21%" in out
