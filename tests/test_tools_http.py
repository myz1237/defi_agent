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


def _tool_call(name: str, args: dict) -> dict:
    return {"name": name, "args": args, "id": "1", "type": "tool_call"}


@respx.mock
def test_lifi_artifact():
    respx.get("https://li.quest/v1/status").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "DONE",
                "sending": {"chainId": 1, "amount": "100", "token": {"symbol": "USDT", "decimals": 6}},
                "receiving": {"chainId": 56, "amount": "200", "token": {"symbol": "BNB", "decimals": 18}},
            },
        )
    )
    msg = lifi_get_status.invoke(_tool_call("lifi_get_status", {"tx_hash": "0xabc"}))
    assert msg.artifact["kind"] == "lifi"
    assert msg.artifact["raw"]["status"] == "DONE"


@respx.mock
def test_morpho_artifact():
    respx.post("https://blue-api.morpho.org/graphql").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "userByAddress": {
                        "address": "0x7b524b0308a776a7d4E65A2Db73bB37881818748",
                        "marketPositions": [
                            {
                                "healthFactor": "1.87",
                                "market": {
                                    "marketId": "0xm",
                                    "lltv": "860000000000000000",
                                    "loanAsset": {"symbol": "RLUSD", "decimals": 18},
                                    "collateralAsset": {"symbol": "cbBTC", "decimals": 8},
                                },
                                "state": {
                                    "collateral": "42500000000",
                                    "collateralUsd": 2000000.0,
                                    "borrowAssets": "1000000000000000000000",
                                    "borrowAssetsUsd": 920000.0,
                                    "supplyAssetsUsd": 0,
                                },
                            }
                        ],
                        "vaultPositions": [],
                    }
                }
            },
        )
    )
    msg = morpho_get_positions.invoke(
        _tool_call("morpho_get_positions", {"address": "0x7b524b0308a776a7d4E65A2Db73bB37881818748"})
    )
    market = msg.artifact["data"]["borrowMarkets"][0]
    assert msg.artifact["kind"] == "morpho"
    assert market["loanSymbol"] == "RLUSD"
    assert market["healthFactor"] == "1.87"
    assert market["lltvPct"] == 86.0
    assert market["ltvPct"] == 46.0
    assert "cbBTC" in market["collateralAmount"]
