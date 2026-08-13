"""Global configuration. Loaded from environment/.env (pydantic-settings).

Key secrets come from .env: DEEPSEEK_API_KEY (read automatically by langchain-deepseek), LANGSMITH_*.
RPC endpoints live in app/chains/registry.py (default public nodes + env overrides).
"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DeepSeek models: flash for routing/guard (fast/cheap), pro for protocol analysis/rendering.
    # Override via env (GUARD_MODEL / AGENT_MODEL) if the DeepSeek model IDs differ.
    guard_model: str = "deepseek-v4-flash"
    agent_model: str = "deepseek-v4-pro"

    # Protocol API endpoints
    lifi_base_url: str = "https://li.quest"  # GET /v1/status
    morpho_graphql_url: str = "https://blue-api.morpho.org/graphql"

    # External HTTP timeout (seconds)
    http_timeout: float = 20.0


settings = Settings()
