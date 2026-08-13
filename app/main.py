"""FastAPI entry point: SSE streaming chat + interrupt resume + three-way identity.

The lifespan opens the async Postgres checkpointer and compiles the graph (singleton).
SSE events: start / token / tool_call / tool_result / interrupt / done / error.
"""

import asyncio
import json
import os
import time
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
from app.api.auth import router as auth_router
from app.api.identity import Identity, get_identity
from app.observability.audit import AuditLog
from app.observability.logging import configure_logging, log_event
from app.storage.repo import touch_thread


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    builder = build_graph()
    audit = AuditLog(os.getenv("LANGGRAPH_PG_DSN"))
    await audit.open()
    app.state.audit = audit
    async with get_async_checkpointer() as cp:
        app.state.graph = builder.compile(checkpointer=cp)
        # Warm the on-device embedding model now so the first knowledge query doesn't pay the load cost.
        try:
            from app.agent.knowledge.embed import embed_query

            await asyncio.to_thread(embed_query, "warmup")
        except Exception as e:  # noqa: BLE001  a warmup failure must not block boot
            log_event("embed_warmup_failed", error=str(e))
        log_event("startup", checkpointer=type(cp).__name__, audit=bool(audit.pool))
        yield
    await audit.close()


app = FastAPI(title="DeFi Agent", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ResumeRequest(BaseModel):
    thread_id: str
    resume: str


def _sse(event: str, payload: dict) -> dict:
    return {"event": event, "data": json.dumps(payload, ensure_ascii=False)}


def _text_of(content) -> str:
    """Extract plain text from message content (some providers may return a list of content blocks)."""
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


_AGENT_NODES = {"wallet_agent", "tx_agent", "knowledge_answer"}


async def _event_stream(graph, payload, config, thread_id: str, identity: Identity, kind: str, message: str):
    """Stream SSE events from the graph and write one audit_log row + structured log per turn.

    Uses two stream modes together:
    - "messages": token-by-token deltas, filtered to the agent nodes (wallet_agent/tx_agent/knowledge_answer)
      so only the assistant's natural-language reply streams (tool-call chunks and the guard call are skipped).
    - "updates": tool_call / tool_result / interrupt, plus the refuse text (refuse is a non-model node,
      so it does not appear in the messages stream).
    """
    started = time.perf_counter()
    intent: str | None = None
    in_scope: bool | None = None
    tools: list[str] = []
    yield _sse("start", {"thread_id": thread_id})
    try:
        async for mode, data in graph.astream(payload, config, stream_mode=["updates", "messages"]):
            if mode == "messages":
                chunk, meta = data
                is_agent = meta.get("langgraph_node") in _AGENT_NODES
                if is_agent and getattr(chunk, "type", "") in ("ai", "AIMessageChunk"):
                    text = _text_of(chunk.content)
                    if text:
                        yield _sse("token", {"text": text})
                continue
            # mode == "updates"
            for node, update in data.items():
                if node == "__interrupt__":
                    intr = update[0]
                    q = intr.value.get("question") if isinstance(intr.value, dict) else str(intr.value)
                    yield _sse("interrupt", {"question": q})
                    continue
                if not isinstance(update, dict):
                    continue
                if node == "guard":
                    intent = update.get("intent", intent)
                    in_scope = update.get("in_scope", in_scope)
                for m in update.get("messages", []) or []:
                    mtype = getattr(m, "type", "")
                    if mtype == "ai" and getattr(m, "tool_calls", None):
                        for tc in m.tool_calls:
                            tools.append(tc["name"])
                            yield _sse("tool_call", {"name": tc["name"], "args": tc.get("args", {})})
                    elif mtype == "ai" and node not in _AGENT_NODES:
                        # Non-model nodes (e.g. refuse) are not in the messages stream; emit their text here.
                        text = _text_of(m.content)
                        if text:
                            yield _sse("token", {"text": text})
                    elif mtype == "tool":
                        art = getattr(m, "artifact", None)
                        if isinstance(art, dict) and art.get("kind"):
                            yield _sse("card", art)
                        content = m.content if isinstance(m.content, str) else str(m.content)
                        yield _sse("tool_result", {"name": getattr(m, "name", ""), "content": content[:1000]})
        yield _sse("done", {})
    except Exception as e:  # noqa: BLE001
        yield _sse("error", {"error": str(e)})
    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        fields = {
            "user_id": identity.user_id,
            "identity_kind": identity.kind,
            "kind": kind,
            "thread_id": thread_id,
            "intent": intent,
            "in_scope": in_scope,
            "tools": tools,
            "latency_ms": latency_ms,
        }
        log_event("chat", **fields)
        await app.state.audit.record(
            user_id=identity.user_id,
            kind=kind,
            thread_id=thread_id,
            intent=intent,
            in_scope=in_scope,
            tools=tools,
            latency_ms=latency_ms,
            message=message,
        )


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    return {"status": "ok" if getattr(app.state, "graph", None) is not None else "starting"}


@app.post("/v1/chat")
async def chat(req: ChatRequest, identity: Identity = Depends(get_identity)):
    thread_id = _scoped_thread(identity, req.thread_id)
    await touch_thread(thread_id, identity.user_id)
    config = {"configurable": {"thread_id": thread_id}}
    payload = {"messages": [HumanMessage(content=req.message)], "connected_address": identity.address}
    return EventSourceResponse(
        _event_stream(app.state.graph, payload, config, thread_id, identity, "chat", req.message)
    )


@app.post("/v1/chat/resume")
async def resume(req: ResumeRequest, identity: Identity = Depends(get_identity)):
    thread_id = _scoped_thread(identity, req.thread_id)
    await touch_thread(thread_id, identity.user_id)
    config = {"configurable": {"thread_id": thread_id}}
    return EventSourceResponse(
        _event_stream(app.state.graph, Command(resume=req.resume), config, thread_id, identity, "resume", req.resume)
    )


@app.get("/v1/threads/{thread_id}/history")
async def history(thread_id: str, identity: Identity = Depends(get_identity)):
    _scoped_thread(identity, thread_id)  # ownership check
    state = await app.state.graph.aget_state({"configurable": {"thread_id": thread_id}})
    msgs = state.values.get("messages", []) if state else []
    return {
        "thread_id": thread_id,
        "messages": [{"type": getattr(m, "type", ""), "content": m.content} for m in msgs],
    }
