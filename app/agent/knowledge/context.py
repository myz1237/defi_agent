"""Contextual Retrieval: generate a short LLM context situating each chunk within its document.

DeepSeek caches request prefixes automatically, so the (per-document, stable) instruction + full document
goes in the system message. We warm that prefix with a single call, then fan the remaining chunks out in
parallel — so they all hit the now-warm cache instead of every parallel call re-processing the document.
"""

import asyncio
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek

from app.agent.prompts import CONTEXT_GEN_INSTRUCTION
from app.config import settings

logger = logging.getLogger(__name__)


def _system(document: str) -> SystemMessage:
    """Instruction + full document — identical across all of a document's chunks, so DeepSeek prefix-caches it."""
    return SystemMessage(content=f"{CONTEXT_GEN_INSTRUCTION}\n\n<document>\n{document}\n</document>")


async def contextualize(document: str, chunks: list[str]) -> list[str]:
    """Return a short situating context for each chunk (empty string where generation failed; caller falls back)."""
    if not chunks:
        return []
    llm = ChatDeepSeek(model=settings.light_model, temperature=0)
    system = _system(document)

    async def gen(chunk: str) -> str:
        try:
            out = await llm.ainvoke([system, HumanMessage(content=f"<chunk>\n{chunk}\n</chunk>")])
            return str(out.content).strip()
        except Exception:  # noqa: BLE001  a context miss must not break ingestion
            logger.exception("context generation failed")
            return ""

    first = await gen(chunks[0])  # warm DeepSeek's prefix cache with the shared system message
    rest = await asyncio.gather(*(gen(c) for c in chunks[1:]))  # then fan out in parallel (cache hits)
    return [first, *rest]
