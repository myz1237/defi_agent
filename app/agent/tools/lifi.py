"""LI.FI 工具:按交易哈希查询跨链转账状态(GET /v1/status)。"""

import httpx
from langchain_core.tools import tool

from app.agent.tools.base import ALL_CHAINS, make_spec
from app.agent.tools.registry import register
from app.config import settings


@tool
def lifi_get_status(tx_hash: str, from_chain: str | None = None, to_chain: str | None = None) -> str:
    """查询 LI.FI 跨链转账状态(PENDING/DONE/FAILED/NOT_FOUND/INVALID)。

    tx_hash: 发送链上的交易哈希。
    from_chain / to_chain: 可选,链 id 或 LI.FI 链 key,提供可加速查询。
    """
    params = {"txHash": tx_hash}
    if from_chain:
        params["fromChain"] = from_chain
    if to_chain:
        params["toChain"] = to_chain
    try:
        resp = httpx.get(f"{settings.lifi_base_url}/v1/status", params=params, timeout=settings.http_timeout)
        data = resp.json()
    except Exception as e:
        return f"LI.FI 状态查询失败:{e}"

    lines = [f"LI.FI status={data.get('status')} substatus={data.get('substatus')}"]
    msg = data.get("substatusMessage") or data.get("message")
    if msg:
        lines.append(f"说明:{msg}")
    if data.get("tool"):
        lines.append(f"bridge/tool={data.get('tool')}")

    for side, label in (("sending", "发送"), ("receiving", "接收")):
        info = data.get(side) or {}
        if info:
            token = (info.get("token") or {}).get("symbol")
            lines.append(
                f"{label}: chainId={info.get('chainId')} txHash={info.get('txHash')} "
                f"token={token} amount(raw)={info.get('amount')}"
            )
    link = data.get("lifiExplorerLink") or data.get("transactionLink")
    if link:
        lines.append(f"explorer: {link}")
    return "\n".join(lines)


register(make_spec(lifi_get_status, "lifi", ALL_CHAINS))
