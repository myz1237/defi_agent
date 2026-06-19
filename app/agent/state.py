"""LangGraph state."""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    in_scope: bool  # scope-guard result
    intent: str  # wallet | transaction | other
    scope_reason: str  # guard reasoning (debugging/observability)
    address: str | None  # extracted wallet address or ENS name
    tx_hash: str | None  # extracted transaction hash
