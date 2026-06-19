"""本地 CLI:与 DeFi Agent 多轮对话(InMemorySaver + interrupt 续跑)。

运行:        uv run python scripts/chat.py
管道冒烟:    printf '问题1\n问题2\n' | uv run python scripts/chat.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import os  # noqa: E402

from langchain_core.messages import HumanMessage  # noqa: E402
from langgraph.types import Command  # noqa: E402

from app.agent.checkpointer import get_checkpointer  # noqa: E402
from app.agent.graph import build_graph  # noqa: E402

# 固定 thread_id:同一 thread 跨进程共享会话历史(Postgres checkpointer 下持久)
CONFIG = {"configurable": {"thread_id": os.getenv("CLI_THREAD_ID", "cli-session")}}


def _print_updates(chunk: dict) -> None:
    for _node, update in chunk.items():
        if not isinstance(update, dict):
            continue
        for m in update.get("messages", []) or []:
            mtype = getattr(m, "type", "")
            tool_calls = getattr(m, "tool_calls", None)
            if mtype == "ai" and tool_calls:
                for tc in tool_calls:
                    print(f"  · 调用工具 {tc['name']}({tc.get('args', {})})")
            elif mtype == "ai" and m.content:
                print(f"\n助手> {m.content}")
            elif mtype == "tool":
                content = m.content if isinstance(m.content, str) else str(m.content)
                preview = content if len(content) <= 400 else content[:400] + " …"
                print(f"  · 工具[{getattr(m, 'name', '')}] -> {preview}")


def _run(graph, payload) -> None:
    while True:
        interrupted = False
        for chunk in graph.stream(payload, CONFIG, stream_mode="updates"):
            if "__interrupt__" in chunk:
                intr = chunk["__interrupt__"][0]
                q = intr.value.get("question") if isinstance(intr.value, dict) else str(intr.value)
                try:
                    answer = input(f"\n[需要补充] {q}\n你> ").strip()
                except EOFError:
                    print("\n(无更多输入,退出)")
                    return
                payload = Command(resume=answer)
                interrupted = True
                break
            _print_updates(chunk)
        if not interrupted:
            return


def main() -> None:
    builder = build_graph()
    with get_checkpointer() as cp:
        graph = builder.compile(checkpointer=cp)
        print(
            f"DeFi Agent CLI(checkpointer={type(cp).__name__}, thread={CONFIG['configurable']['thread_id']})"
            " — 输入钱包/交易相关问题;Ctrl-D 退出"
        )
        while True:
            try:
                user = input("\n你> ").strip()
            except EOFError:
                print("\n再见")
                break
            if not user:
                continue
            _run(graph, {"messages": [HumanMessage(content=user)]})


if __name__ == "__main__":
    main()
