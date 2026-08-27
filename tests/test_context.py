"""Unit tests for Contextual Retrieval context generation (LLM mocked — offline)."""

import asyncio

from langchain_core.messages import AIMessage

import app.agent.knowledge.context as ctx


def test_contextualize_returns_one_context_per_chunk_in_order(monkeypatch):
    class _LLM:
        async def ainvoke(self, msgs):
            chunk = msgs[-1].content  # the HumanMessage carries the chunk
            return AIMessage(content=f"ctx:{chunk}")

    monkeypatch.setattr(ctx, "ChatDeepSeek", lambda **_k: _LLM())
    out = asyncio.run(ctx.contextualize("DOC", ["alpha", "beta", "gamma"]))
    assert len(out) == 3
    assert out[0].startswith("ctx:") and "alpha" in out[0] and "gamma" in out[2]


def test_contextualize_returns_empty_string_on_failure(monkeypatch):
    class _Boom:
        async def ainvoke(self, _msgs):
            raise RuntimeError("provider down")

    monkeypatch.setattr(ctx, "ChatDeepSeek", lambda **_k: _Boom())
    assert asyncio.run(ctx.contextualize("DOC", ["a", "b"])) == ["", ""]


def test_contextualize_empty_input():
    assert asyncio.run(ctx.contextualize("DOC", [])) == []
