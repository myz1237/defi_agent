import asyncio

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

import app.agent.graph as graph_mod
from app.agent.graph import (
    ScopeDecision,
    _recent_transcript,
    _rewrite_query,
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


def test_extract_wallet_ens_resolves_to_address(monkeypatch):
    # An ENS is resolved to its canonical 0x address and stored (not the ENS name).
    monkeypatch.setattr(graph_mod, "resolve_ens_address", lambda _n: "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
    assert extract_wallet(_state("balances of vitalik.eth"))["address"] == "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def test_extract_wallet_ens_falls_back_to_name_when_unresolved(monkeypatch):
    monkeypatch.setattr(graph_mod, "resolve_ens_address", lambda _n: None)
    assert extract_wallet(_state("balances of nope.eth"))["address"] == "nope.eth"


def test_extract_wallet_none():
    assert extract_wallet(_state("show my wallet"))["address"] is None


def test_extract_wallet_reuses_prior_resolved_address():
    # A follow-up with no address reuses the previously resolved 0x (not clobbered to None).
    prior = "0xABCabc0000000000000000000000000000000000"
    state = {"messages": [HumanMessage(content="check its balance")], "address": prior}
    assert extract_wallet(state)["address"] == prior


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
        def with_structured_output(self, _schema, **_kw):
            return self

        def invoke(self, _msgs):
            return ScopeDecision(in_scope=True, intent="knowledge", protocol="morpho", reason="concept q")

    monkeypatch.setattr(graph_mod, "ChatDeepSeek", lambda **_k: _FakeLLM())
    out = guard_scope(_state("how does morpho liquidation work"))
    assert out == {"in_scope": True, "intent": "knowledge", "protocol": "morpho", "scope_reason": "concept q"}


def test_recent_transcript_takes_last_n_and_labels_roles():
    msgs = [HumanMessage(content="q1"), AIMessage(content="a1"), HumanMessage(content="q2")]
    t = _recent_transcript(msgs, n=2)
    assert "Assistant: a1" in t and "User: q2" in t and "q1" not in t


# A multi-turn history (so rewrite actually fires; single-turn is skipped by design).
_FOLLOWUP = [
    HumanMessage(content="What is Morpho liquidation?"),
    AIMessage(content="It repays unhealthy positions."),
    HumanMessage(content="how does it get triggered"),
]


def test_rewrite_query_skips_first_turn(monkeypatch):
    # First turn has no context to resolve — return the raw question WITHOUT calling the LLM.
    class _BoomLLM:
        async def ainvoke(self, _msgs, **_kw):
            raise AssertionError("LLM should not be called on the first turn")

    monkeypatch.setattr(graph_mod, "ChatDeepSeek", lambda **_k: _BoomLLM())
    assert asyncio.run(_rewrite_query([HumanMessage(content="What is Morpho Blue?")])) == "What is Morpho Blue?"


def test_rewrite_query_returns_model_output_on_followup(monkeypatch):
    class _LLM:
        async def ainvoke(self, _msgs, **_kw):
            return AIMessage(content="  Morpho liquidation trigger conditions  ")

    monkeypatch.setattr(graph_mod, "ChatDeepSeek", lambda **_k: _LLM())
    assert asyncio.run(_rewrite_query(_FOLLOWUP)) == "Morpho liquidation trigger conditions"


def test_rewrite_query_falls_back_to_raw_on_error_or_empty(monkeypatch):
    class _BoomLLM:
        async def ainvoke(self, _msgs, **_kw):
            raise RuntimeError("provider down")

    monkeypatch.setattr(graph_mod, "ChatDeepSeek", lambda **_k: _BoomLLM())
    assert asyncio.run(_rewrite_query(_FOLLOWUP)) == "how does it get triggered"

    class _EmptyLLM:
        async def ainvoke(self, _msgs, **_kw):
            return AIMessage(content="   ")

    monkeypatch.setattr(graph_mod, "ChatDeepSeek", lambda **_k: _EmptyLLM())
    assert asyncio.run(_rewrite_query(_FOLLOWUP)) == "how does it get triggered"


def test_guard_scope_fails_closed_on_bad_output(monkeypatch):
    """If the guard model returns unparseable JSON (json_mode has no API schema enforcement), refuse — don't crash."""

    class _BoomLLM:
        def with_structured_output(self, _schema, **_kw):
            return self

        def invoke(self, _msgs):
            raise ValueError("model returned non-JSON prose")

    monkeypatch.setattr(graph_mod, "ChatDeepSeek", lambda **_k: _BoomLLM())
    out = guard_scope(_state("show my Morpho positions"))
    assert out["in_scope"] is False and out["intent"] == "other"


def test_has_helpers():
    assert has_address({"address": "0x1"}) == "yes"
    assert has_address({}) == "no"
    assert has_tx({"tx_hash": "0x1"}) == "yes"
    assert has_tx({}) == "no"


def _graph_with_stubbed_llm(monkeypatch):
    """Build the real graph with every LLM-backed node stubbed, so routing can be tested without network."""

    def fake_guard(state):
        text = graph_mod._last_human_text(state["messages"])
        return {
            "in_scope": True,
            "intent": "wallet" if ".eth" in text else "transaction",
            "protocol": "none",
            "scope_reason": "stub",
        }

    monkeypatch.setattr(graph_mod, "guard_scope", fake_guard)
    monkeypatch.setattr(graph_mod, "resolve_ens_address", lambda _n: "0x" + "a" * 40)
    monkeypatch.setattr(graph_mod, "wallet_agent", lambda _s: {"messages": [AIMessage(content="wallet done")]})
    monkeypatch.setattr(graph_mod, "tx_agent", lambda _s: {"messages": [AIMessage(content="tx done")]})
    return graph_mod.build_graph().compile(checkpointer=InMemorySaver())


def test_clarify_reroutes_when_answered_with_a_different_question(monkeypatch):
    """Answering a clarification with an unrelated question must re-guard and re-route.

    Regression: clarify_* used to loop back to the extractor, so the thread stayed wedged on the same
    interrupt forever with intent/protocol frozen at the first turn.
    """
    g = _graph_with_stubbed_llm(monkeypatch)
    cfg = {"configurable": {"thread_id": "reroute"}}

    out = g.invoke({"messages": [HumanMessage(content="Check LIFI tx status 0x1231")]}, cfg)
    assert out["__interrupt__"], "a too-short hash should trigger the clarify interrupt"
    assert g.get_state(cfg).next == ("clarify_tx",)

    g.invoke(Command(resume="check myz1237.eth Morpho position"), cfg)
    state = g.get_state(cfg)
    assert state.next == ()  # the run completed instead of interrupting again
    assert state.values["intent"] == "wallet"  # guard re-ran on the new question
    assert state.values["messages"][-1].content == "wallet done"


def test_clarify_proceeds_when_answered_with_the_missing_hash(monkeypatch):
    g = _graph_with_stubbed_llm(monkeypatch)
    cfg = {"configurable": {"thread_id": "answered"}}

    g.invoke({"messages": [HumanMessage(content="Check LIFI tx status 0x1231")]}, cfg)
    g.invoke(Command(resume="0x" + "b" * 64), cfg)

    state = g.get_state(cfg)
    assert state.next == ()
    assert state.values["tx_hash"] == "0x" + "b" * 64
    assert state.values["messages"][-1].content == "tx done"
