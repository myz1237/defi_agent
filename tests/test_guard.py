"""Guard classification checks against the real guard model (skipped without ANTHROPIC_API_KEY).

Doubles as the routing eval for the knowledge intent: it asserts the guard labels conceptual protocol
questions as in-scope `knowledge` with the right protocol, and keeps wallet/tx/off-topic classified as before.
"""

import os

import pytest
from langchain_core.messages import HumanMessage

from app.agent.graph import guard_scope

pytestmark = pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="no ANTHROPIC_API_KEY")


def _guard(text: str) -> dict:
    return guard_scope({"messages": [HumanMessage(content=text)]})


@pytest.mark.parametrize(
    ("text", "protocol"),
    [
        ("How does Morpho liquidation work?", "morpho"),
        ("What does a PENDING LI.FI transfer status mean?", "lifi"),
        ("What is LLTV on Morpho?", "morpho"),
    ],
)
def test_knowledge_questions_are_in_scope_knowledge(text, protocol):
    d = _guard(text)
    assert d["in_scope"] is True
    assert d["intent"] == "knowledge"
    assert d["protocol"] == protocol


def test_wallet_and_tx_and_offtopic_still_classified():
    assert _guard("Show my Morpho positions")["intent"] == "wallet"
    assert _guard("status of 0x" + "a" * 64)["intent"] == "transaction"
    assert _guard("What's the weather today?")["in_scope"] is False
