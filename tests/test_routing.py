from langchain_core.messages import HumanMessage

from app.agent.graph import extract_tx, extract_wallet, has_address, has_tx, route_after_guard


def _state(text: str) -> dict:
    return {"messages": [HumanMessage(content=text)]}


def test_extract_wallet_address():
    s = extract_wallet(_state("check 0x7b524b0308a776a7d4E65A2Db73bB37881818748 please"))
    assert s["address"] == "0x7b524b0308a776a7d4E65A2Db73bB37881818748"


def test_extract_wallet_ens():
    assert extract_wallet(_state("balances of vitalik.eth"))["address"] == "vitalik.eth"


def test_extract_wallet_none():
    assert extract_wallet(_state("show my wallet"))["address"] is None


def test_extract_tx_hash():
    h = "0x" + "a" * 64
    assert extract_tx(_state(f"status of {h}"))["tx_hash"] == h


def test_extract_tx_rejects_address_length():
    # A 40-hex address must not be mistaken for a 64-hex tx hash.
    assert extract_tx(_state("0x" + "a" * 40))["tx_hash"] is None


def test_route_after_guard():
    assert route_after_guard({"in_scope": False, "intent": "other"}) == "refuse"
    assert route_after_guard({"in_scope": True, "intent": "wallet"}) == "wallet"
    assert route_after_guard({"in_scope": True, "intent": "transaction"}) == "transaction"


def test_has_helpers():
    assert has_address({"address": "0x1"}) == "yes"
    assert has_address({}) == "no"
    assert has_tx({"tx_hash": "0x1"}) == "yes"
    assert has_tx({}) == "no"
