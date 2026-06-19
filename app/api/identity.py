"""三态身份依赖:widget(API key)/ SIWE(JWT)/ 匿名会话。

最小可用版:
- X-API-Key 命中 WIDGET_API_KEYS(逗号分隔 env)→ widget 身份。
- Authorization: Bearer <jwt> → siwe 身份(完整 SIWE 验签留待 M8 前端联调,这里仅取 sub)。
- 否则匿名:用 X-Session-Id(无则新生成)派生稳定 user_id。
限流分档可按 identity.kind 实现(后续)。
"""

import os
import uuid
from dataclasses import dataclass

from fastapi import Header, Request


@dataclass(frozen=True)
class Identity:
    kind: str  # widget | siwe | anon
    user_id: str
    session_id: str


def _widget_keys() -> set[str]:
    raw = os.getenv("WIDGET_API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


async def get_identity(
    request: Request,
    x_api_key: str | None = Header(default=None),
    x_session_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> Identity:
    if x_api_key and x_api_key in _widget_keys():
        return Identity(kind="widget", user_id=f"widget:{x_api_key[:8]}", session_id=x_api_key[:8])

    if authorization and authorization.lower().startswith("bearer "):
        # TODO(M8): 校验 SIWE 签发的 JWT;此处先取 token 末段作占位 user_id
        token = authorization.split(" ", 1)[1]
        return Identity(kind="siwe", user_id=f"siwe:{token[-12:]}", session_id=token[-12:])

    session_id = x_session_id or f"anon-{uuid.uuid4().hex[:16]}"
    return Identity(kind="anon", user_id=f"anon:{session_id}", session_id=session_id)
