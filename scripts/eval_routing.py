"""Routing eval: run guard_scope over labeled prompts and report accuracy.

Doubles as a regression check for the scope guard. Real LLM calls (the DeepSeek guard model); LangSmith
tracing is captured automatically when LANGSMITH_TRACING is enabled.

Run: uv run python scripts/eval_routing.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage  # noqa: E402

from app.agent.graph import guard_scope  # noqa: E402

# (prompt, expected_route) where route is one of: wallet | transaction | knowledge | refuse
CASES: list[tuple[str, str]] = [
    ("What's the weather today?", "refuse"),
    ("Tell me a joke", "refuse"),
    ("Buy me 1 ETH", "refuse"),  # write operation
    ("What's my Aave deposit?", "refuse"),  # unsupported protocol
    ("Show Solana balance of abc123", "refuse"),  # unsupported chain
    ("Is tx 0x7459b8d8fa53ca8d9d3fbcb835b28cedb12f0fb34bdd4dcb5579a8ebb87a1abd cross-chain?", "transaction"),
    ("Decode transaction 0xabcabcabcabcabcabc", "transaction"),
    ("Show the logs for tx 0xdeadbeef", "transaction"),
    ("What's the LI.FI status of 0x123?", "transaction"),
    ("Show Morpho positions for 0x7b524b0308a776a7d4E65A2Db73bB37881818748", "wallet"),
    ("What are vitalik.eth's balances?", "wallet"),
    ("Does 0x0d49928a6037b35b0bdbc82b439d7c5d108bee9c have any Morpho debt?", "wallet"),
    ("How does Morpho liquidation work?", "knowledge"),  # conceptual, no address/hash
    ("What does a PENDING LI.FI transfer status mean?", "knowledge"),
]


def route_of(decision: dict) -> str:
    if not decision.get("in_scope"):
        return "refuse"
    return decision.get("intent", "other")


def main() -> None:
    correct = 0
    print(f"Running {len(CASES)} routing cases...\n")
    for prompt, expected in CASES:
        decision = guard_scope({"messages": [HumanMessage(content=prompt)]})
        got = route_of(decision)
        ok = got == expected
        correct += ok
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] expected={expected:<11} got={got:<11} | {prompt[:60]}")
    acc = correct / len(CASES)
    print(f"\nAccuracy: {correct}/{len(CASES)} = {acc:.0%}")
    sys.exit(0 if correct == len(CASES) else 1)


if __name__ == "__main__":
    main()
