from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "InferOps AI"
    environment: str = "local"

    openai_api_key: str | None = None
    default_provider: str = "mock"

    database_url: str = "sqlite+aiosqlite:///./inferops.db"
    redis_url: str = "redis://redis:6379/0"

    ollama_base_url: str = "http://localhost:11434"
    vllm_base_url: str = "http://localhost:8001/v1"

    backend_cors_origins: str = "http://localhost:3000"

    qdrant_url: str = "http://qdrant:6333"
    rag_collection_name: str = "inferops_knowledge"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    ollama_cloud_base_url: str = "https://ollama.com"
    ollama_cloud_api_key: str | None = None
    ollama_cloud_model: str = "gpt-oss:120b-cloud"

    user_daily_budget_usd: float = Field(default=1.0)
    team_monthly_budget_usd: float = Field(default=50.0)

    # ── Cloud (aws-deploy branch) ────────────────────────────────────────────
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    sqs_queue_url: str | None = None
    aws_region: str = "eu-central-1"

    log_level: str = "INFO"
    max_daily_budget_usd: float = 5.0

    @property
    def is_cloud(self) -> bool:
        return self.environment in {"demo", "production", "staging", "aws-deploy"}

    @property
    def is_local(self) -> bool:
        return not self.is_cloud

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
