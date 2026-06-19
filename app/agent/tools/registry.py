"""工具注册表:按协议分组、按链筛选,供各 agent 绑定其允许的只读工具。

各工具模块在导入时调用 register() 落册;`app.agent.tools` 包的 __init__ 负责
导入这些模块以触发注册。
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
    """返回匹配的 langchain 工具列表。

    protocols: 仅取这些协议(None=全部)。
    chain: 规范链键,仅取支持该链的工具(None=不按链过滤)。
    """
    specs = _REGISTRY
    if protocols is not None:
        wanted = set(protocols)
        specs = [s for s in specs if s.protocol in wanted]
    if chain is not None:
        specs = [s for s in specs if s.supports_chain(chain)]
    return [s.tool for s in specs]
