"""LangGraph state."""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    in_scope: bool  # scope-guard result
    intent: str  # wallet | transaction | knowledge | other
    protocol: str  # lifi | morpho | both | none (which docs a knowledge question is about)
    scope_reason: str  # guard reasoning (debugging/observability)
    address: str | None  # extracted wallet address or ENS name
    tx_hash: str | None  # extracted transaction hash
    connected_address: str | None  # connected (SIWE) wallet address, used as fallback for "my ..." queries
    knowledge_context: str  # retrieved doc chunks (formatted) for the knowledge line to answer from
