"""工具元数据与规格。与 langchain 工具解耦,便于按协议/链筛选与扩展。

加新协议 = 新建 tools/<protocol>/ 模块,用 @register_tool 注册若干工具即可,
图结构不变(见 registry.get_tools)。
"""

from collections.abc import Sequence
from dataclasses import dataclass

from langchain_core.tools import BaseTool

# 受支持协议(支持范围真值来源之一)
PROTOCOLS = ("explorer", "lifi", "morpho")

# supported_chains 用此通配表示"所有受支持链"
ALL_CHAINS = ("*",)


@dataclass(frozen=True)
class ToolSpec:
    tool: BaseTool
    protocol: str  # explorer | lifi | morpho
    supported_chains: tuple[str, ...]  # 规范链键元组,或 ALL_CHAINS
    read_only: bool = True  # 本项目所有工具均只读

    def supports_chain(self, chain_key: str) -> bool:
        return "*" in self.supported_chains or chain_key in self.supported_chains


def make_spec(
    tool: BaseTool,
    protocol: str,
    supported_chains: Sequence[str] = ALL_CHAINS,
) -> ToolSpec:
    if protocol not in PROTOCOLS:
        raise ValueError(f"未知协议 {protocol!r},应为 {PROTOCOLS}")
    return ToolSpec(tool=tool, protocol=protocol, supported_chains=tuple(supported_chains), read_only=True)
