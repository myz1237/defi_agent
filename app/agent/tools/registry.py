"""Tool registry: grouped by protocol, filtered by chain, so each agent binds its allowed read-only tools.

Each tool module calls register() at import time; the `app.agent.tools` package __init__ imports
those modules to trigger registration.
"""

from collections.abc import Iterable

from langchain_core.tools import BaseTool

from app.agent.tools.base import ToolSpec

_REGISTRY: list[ToolSpec] = []


def register(spec: ToolSpec) -> ToolSpec:
    _REGISTRY.append(spec)
    return spec


def all_specs() -> list[ToolSpec]:
    return list(_REGISTRY)


def get_tools(
    protocols: Iterable[str] | None = None,
    chain: str | None = None,
) -> list[BaseTool]:
    """Return the list of matching langchain tools.

    protocols: only these protocols (None = all).
    chain: canonical chain key, only tools supporting that chain (None = no chain filtering).
    """
    specs = _REGISTRY
    if protocols is not None:
        wanted = set(protocols)
        specs = [s for s in specs if s.protocol in wanted]
    if chain is not None:
        specs = [s for s in specs if s.supports_chain(chain)]
    return [s.tool for s in specs]
