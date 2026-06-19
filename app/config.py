"""Global configuration. Loaded from environment/.env (pydantic-settings).

Key secrets come from .env: ANTHROPIC_API_KEY (read automatically by langchain-anthropic), LANGSMITH_*.
RPC endpoints live in app/chains/registry.py (default public nodes + env overrides).
"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Models: haiku for routing/guard (fast/cheap), sonnet for protocol analysis/rendering (default). No Opus.
    guard_model: str = "claude-haiku-4-5-20251001"
    agent_model: str = "claude-sonnet-4-6"

    # Protocol API endpoints
    lifi_base_url: str = "https://li.quest"  # GET /v1/status
    morpho_graphql_url: str = "https://blue-api.morpho.org/graphql"

    # External HTTP timeout (seconds)
    http_timeout: float = 20.0


settings = Settings()
