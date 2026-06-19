"""DeFi Agent graph: deterministic routing (guard/classify/extract) + protocol tool agents (wallet/tx lines).

- system+tools use Anthropic prompt caching (_cached_system sets the cache breakpoint, dynamic content after it).
- interrupt() handles missing input.
- Exports `graph` (for LangGraph Studio; the platform provides its own persistence, so no checkpointer bound).
"""

import re
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt
from pydantic import BaseModel, Field

import app.agent.tools  # noqa: F401  trigger tool registration
from app.agent.prompts import GUARD_PROMPT, REFUSE_TEXT, TX_SYSTEM, WALLET_SYSTEM
from app.agent.state import AgentState
from app.agent.tools.explorer import get_balances, resolve_ens
from app.agent.tools.registry import get_tools
from app.config import settings

TX_HASH_RE = re.compile(r"0x[a-fA-F0-9]{64}")
ADDRESS_RE = re.compile(r"0x[a-fA-F0-9]{40}(?![a-fA-F0-9])")
ENS_RE = re.compile(r"\b[a-zA-Z0-9-]+\.eth\b")

# Wallet line: Morpho + balance + ENS resolution; tx line: all read-only tools
WALLET_TOOLS = get_tools(["morpho"]) + [resolve_ens, get_balances]
TX_TOOLS = get_tools(["explorer", "lifi", "morpho"])


def _cached_system(static_text: str, dynamic_text: str | None = None) -> SystemMessage:
    """Cache the system message with cache_control; Anthropic caches the tools+system prefix together.
    Dynamic content goes after the cache breakpoint to avoid busting the cache."""
    blocks: list[dict] = [{"type": "text", "text": static_text, "cache_control": {"type": "ephemeral"}}]
    if dynamic_text:
        blocks.append({"type": "text", "text": dynamic_text})
    return SystemMessage(content=blocks)


def _last_human_text(messages) -> str:
    for m in reversed(messages):
        if getattr(m, "type", "") == "human":
            return m.content if isinstance(m.content, str) else str(m.content)
    return ""


# ---------- Guard / classify ----------
class ScopeDecision(BaseModel):
    in_scope: bool = Field(description="whether it is within the supported scope")
    intent: Literal["wallet", "transaction", "other"]
    reason: str = Field(description="short reason")


def guard_scope(state: AgentState) -> dict:
    llm = ChatAnthropic(model=settings.guard_model, temperature=0).with_structured_output(ScopeDecision)
    decision: ScopeDecision = llm.invoke([_cached_system(GUARD_PROMPT), *state["messages"]])
    return {"in_scope": decision.in_scope, "intent": decision.intent, "scope_reason": decision.reason}


def route_after_guard(state: AgentState) -> str:
    if not state.get("in_scope"):
        return "refuse"
    return "wallet" if state.get("intent") == "wallet" else "transaction"


def refuse(state: AgentState) -> dict:
    return {"messages": [AIMessage(content=REFUSE_TEXT)]}


# ---------- Wallet line ----------
def extract_wallet(state: AgentState) -> dict:
    text = _last_human_text(state["messages"])
    m = ADDRESS_RE.search(text) or ENS_RE.search(text)
    return {"address": m.group(0) if m else None}


def has_address(state: AgentState) -> str:
    return "yes" if state.get("address") else "no"


def clarify_wallet(state: AgentState) -> dict:
    answer = interrupt(
        {"question": "No wallet address detected. Please provide a 0x address or ENS name (e.g. vitalik.eth)."}
    )
    return {"messages": [HumanMessage(content=str(answer))]}


def wallet_agent(state: AgentState) -> dict:
    llm = ChatAnthropic(model=settings.agent_model, temperature=0).bind_tools(WALLET_TOOLS)
    sys = _cached_system(WALLET_SYSTEM, f"Known wallet address/ENS: {state.get('address')}")
    return {"messages": [llm.invoke([sys, *state["messages"]])]}


# ---------- Transaction line ----------
def extract_tx(state: AgentState) -> dict:
    text = _last_human_text(state["messages"])
    m = TX_HASH_RE.search(text)
    return {"tx_hash": m.group(0) if m else None}


def has_tx(state: AgentState) -> str:
    return "yes" if state.get("tx_hash") else "no"


def clarify_tx(state: AgentState) -> dict:
    answer = interrupt(
        {"question": "No transaction hash detected. Please provide a 66-character transaction hash starting with 0x."}
    )
    return {"messages": [HumanMessage(content=str(answer))]}


def tx_agent(state: AgentState) -> dict:
    llm = ChatAnthropic(model=settings.agent_model, temperature=0).bind_tools(TX_TOOLS)
    sys = _cached_system(TX_SYSTEM, f"Known transaction hash: {state.get('tx_hash')}")
    return {"messages": [llm.invoke([sys, *state["messages"]])]}


def build_graph() -> StateGraph:
    b = StateGraph(AgentState)
    b.add_node("guard", guard_scope)
    b.add_node("refuse", refuse)
    b.add_node("extract_wallet", extract_wallet)
    b.add_node("clarify_wallet", clarify_wallet)
    b.add_node("wallet_agent", wallet_agent)
    b.add_node("wallet_tools", ToolNode(WALLET_TOOLS))
    b.add_node("extract_tx", extract_tx)
    b.add_node("clarify_tx", clarify_tx)
    b.add_node("tx_agent", tx_agent)
    b.add_node("tx_tools", ToolNode(TX_TOOLS))

    b.add_edge(START, "guard")
    b.add_conditional_edges(
        "guard",
        route_after_guard,
        {"refuse": "refuse", "wallet": "extract_wallet", "transaction": "extract_tx"},
    )
    b.add_edge("refuse", END)

    b.add_conditional_edges("extract_wallet", has_address, {"yes": "wallet_agent", "no": "clarify_wallet"})
    b.add_edge("clarify_wallet", "extract_wallet")
    b.add_conditional_edges("wallet_agent", tools_condition, {"tools": "wallet_tools", END: END})
    b.add_edge("wallet_tools", "wallet_agent")

    b.add_conditional_edges("extract_tx", has_tx, {"yes": "tx_agent", "no": "clarify_tx"})
    b.add_edge("clarify_tx", "extract_tx")
    b.add_conditional_edges("tx_agent", tools_condition, {"tools": "tx_tools", END: END})
    b.add_edge("tx_tools", "tx_agent")
    return b


# For LangGraph Studio (langgraph dev); the platform provides persistence, so no checkpointer bound
graph = build_graph().compile()
