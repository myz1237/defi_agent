from langchain_core.messages import HumanMessage

import app.agent.graph as graph_mod
from app.agent.graph import (
    ScopeDecision,
    extract_tx,
    extract_wallet,
    format_context,
    guard_scope,
    has_address,
    has_tx,
    route_after_guard,
)
from app.agent.knowledge.store import RetrievedChunk


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
    assert route_after_guard({"in_scope": True, "intent": "knowledge"}) == "knowledge"


def test_format_context_labels_and_orders_sources():
    chunks = [
        RetrievedChunk("morpho", "Liquidation", "Overview", "https://docs.morpho.org/liq", "body A"),
        RetrievedChunk("lifi", None, "Status", "https://docs.li.fi/status", "body B"),
    ]
    out = format_context(chunks)
    assert "[Source 1] Liquidation — https://docs.morpho.org/liq" in out
    assert "[Source 2] Status — https://docs.li.fi/status" in out  # falls back to section when title is None
    assert "body A" in out and "body B" in out


def test_format_context_empty():
    assert format_context([]) == ""


def test_format_context_shares_source_number_for_same_url(monkeypatch):
    url = "https://docs.morpho.org/liq"
    chunks = [
        RetrievedChunk("morpho", "Liquidation", "Overview", url, "part one"),
        RetrievedChunk("morpho", "Liquidation", "Process", url, "part two"),
    ]
    out = format_context(chunks)
    # both chunks from the same doc share [Source 1], so the model's unique Sources list stays clean
    assert out.count("[Source 1]") == 2
    assert "[Source 2]" not in out


def test_guard_scope_maps_structured_decision(monkeypatch):
    """guard_scope propagates the structured decision (incl. protocol) into state — offline, no API call."""

    class _FakeLLM:
        def with_structured_output(self, _schema):
            return self

        def invoke(self, _msgs):
            return ScopeDecision(in_scope=True, intent="knowledge", protocol="morpho", reason="concept q")

    monkeypatch.setattr(graph_mod, "ChatAnthropic", lambda **_k: _FakeLLM())
    out = guard_scope(_state("how does morpho liquidation work"))
    assert out == {"in_scope": True, "intent": "knowledge", "protocol": "morpho", "scope_reason": "concept q"}


def test_has_helpers():
    assert has_address({"address": "0x1"}) == "yes"
    assert has_address({}) == "no"
    assert has_tx({"tx_hash": "0x1"}) == "yes"
    assert has_tx({}) == "no"
