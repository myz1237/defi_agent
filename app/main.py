"""FastAPI entry point: SSE streaming chat + interrupt resume + three-way identity.

The lifespan opens the async Postgres checkpointer and compiles the graph (singleton).
SSE events: start / token / tool_call / tool_result / interrupt / done / error.
"""

import json
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agent.checkpointer import get_async_checkpointer
from app.agent.graph import build_graph
from app.api.identity import Identity, get_identity


@asynccontextmanager
async def lifespan(app: FastAPI):
    builder = build_graph()
    async with get_async_checkpointer() as cp:
        app.state.graph = builder.compile(checkpointer=cp)
        yield


app = FastAPI(title="DeFi Agent", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ResumeRequest(BaseModel):
    thread_id: str
    resume: str


def _sse(event: str, payload: dict) -> dict:
    return {"event": event, "data": json.dumps(payload, ensure_ascii=False)}


def _text_of(content) -> str:
    """Extract plain text from message content (Anthropic may return a list of content blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _scoped_thread(identity: Identity, thread_id: str | None) -> str:
    """Thread ownership isolation: an existing thread must belong to the current identity,
    otherwise create a new thread prefixed with the identity."""
    if thread_id:
        if not thread_id.startswith(f"{identity.user_id}::"):
            raise HTTPException(status_code=403, detail="thread does not belong to the current identity")
        return thread_id
    return f"{identity.user_id}::{uuid.uuid4().hex[:16]}"


async def _event_stream(graph, payload, config, thread_id: str):
    """Map updates mode to SSE: tool_call / tool_result / token (assistant reply) / interrupt.

    Note: nodes use synchronous non-streaming invoke, so the assistant reply is emitted as a single token event;
    true token-by-token streaming would require switching nodes to streaming model calls (future enhancement).
    """
    yield _sse("start", {"thread_id": thread_id})
    try:
        async for update_dict in graph.astream(payload, config, stream_mode="updates"):
            for node, update in update_dict.items():
                if node == "__interrupt__":
                    intr = update[0]
                    q = intr.value.get("question") if isinstance(intr.value, dict) else str(intr.value)
                    yield _sse("interrupt", {"question": q})
                    continue
                if not isinstance(update, dict):
                    continue
                for m in update.get("messages", []) or []:
                    mtype = getattr(m, "type", "")
                    if mtype == "ai" and getattr(m, "tool_calls", None):
                        for tc in m.tool_calls:
                            yield _sse("tool_call", {"name": tc["name"], "args": tc.get("args", {})})
                    elif mtype == "ai":
                        text = _text_of(m.content)
                        if text:
                            yield _sse("token", {"text": text})
                    elif mtype == "tool":
                        content = m.content if isinstance(m.content, str) else str(m.content)
                        yield _sse("tool_result", {"name": getattr(m, "name", ""), "content": content[:1000]})
        yield _sse("done", {})
    except Exception as e:  # noqa: BLE001
        yield _sse("error", {"error": str(e)})


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    return {"status": "ok" if getattr(app.state, "graph", None) is not None else "starting"}


@app.post("/v1/chat")
async def chat(req: ChatRequest, identity: Identity = Depends(get_identity)):
    thread_id = _scoped_thread(identity, req.thread_id)
    config = {"configurable": {"thread_id": thread_id}}
    payload = {"messages": [HumanMessage(content=req.message)]}
    return EventSourceResponse(_event_stream(app.state.graph, payload, config, thread_id))


@app.post("/v1/chat/resume")
async def resume(req: ResumeRequest, identity: Identity = Depends(get_identity)):
    thread_id = _scoped_thread(identity, req.thread_id)
    config = {"configurable": {"thread_id": thread_id}}
    return EventSourceResponse(_event_stream(app.state.graph, Command(resume=req.resume), config, thread_id))


@app.get("/v1/threads/{thread_id}/history")
async def history(thread_id: str, identity: Identity = Depends(get_identity)):
    _scoped_thread(identity, thread_id)  # ownership check
    state = await app.state.graph.aget_state({"configurable": {"thread_id": thread_id}})
    msgs = state.values.get("messages", []) if state else []
    return {
        "thread_id": thread_id,
        "messages": [{"type": getattr(m, "type", ""), "content": m.content} for m in msgs],
    }
