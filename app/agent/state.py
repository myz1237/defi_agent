"""LangGraph 状态。"""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    in_scope: bool  # 越界守卫结果
    intent: str  # wallet | transaction | other
    scope_reason: str  # 守卫理由(调试/可观测)
    address: str | None  # 抽取到的钱包地址或 ENS 域名
    tx_hash: str | None  # 抽取到的交易哈希
