"""Tool metadata and specs. Decoupled from langchain tools to ease filtering/extension by protocol/chain.

Adding a protocol = create a tools/<protocol>/ module and register a few tools with @register_tool;
the graph structure stays the same (see registry.get_tools).
"""

from collections.abc import Sequence
from dataclasses import dataclass

from langchain_core.tools import BaseTool

# Supported protocols (one of the sources of truth for supported scope)
PROTOCOLS = ("explorer", "lifi", "morpho")

# supported_chains uses this wildcard to mean "all supported chains"
ALL_CHAINS = ("*",)


@dataclass(frozen=True)
class ToolSpec:
    tool: BaseTool
    protocol: str  # explorer | lifi | morpho
    supported_chains: tuple[str, ...]  # tuple of canonical chain keys, or ALL_CHAINS
    read_only: bool = True  # all tools in this project are read-only

    def supports_chain(self, chain_key: str) -> bool:
        return "*" in self.supported_chains or chain_key in self.supported_chains


def make_spec(
    tool: BaseTool,
    protocol: str,
    supported_chains: Sequence[str] = ALL_CHAINS,
) -> ToolSpec:
    if protocol not in PROTOCOLS:
        raise ValueError(f"Unknown protocol {protocol!r}, expected one of {PROTOCOLS}")
    return ToolSpec(tool=tool, protocol=protocol, supported_chains=tuple(supported_chains), read_only=True)
