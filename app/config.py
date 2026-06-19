"""全局配置。从环境/.env 读取(pydantic-settings)。

关键 key 由 .env 提供:ANTHROPIC_API_KEY(langchain-anthropic 自动读取)、LANGSMITH_*。
RPC 端点见 app/chains/registry.py(默认公共节点 + env 覆盖)。
"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 模型:路由/守卫用 haiku(快/省),协议分析/渲染用 sonnet(默认)。不用 Opus。
    guard_model: str = "claude-haiku-4-5-20251001"
    agent_model: str = "claude-sonnet-4-6"

    # 协议 API 端点
    lifi_base_url: str = "https://li.quest"  # GET /v1/status
    morpho_graphql_url: str = "https://blue-api.morpho.org/graphql"

    # 外部 HTTP 超时(秒)
    http_timeout: float = 20.0


settings = Settings()
