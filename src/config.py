from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6-20250514"
    llm_model_fast: str = "claude-haiku-4-5-20251001"
    embedding_model: str = "text-embedding-3-small"

    # Database
    database_url: str = "sqlite:///data/agentflow.db"
    qdrant_path: str = "./data/qdrant"

    # Observability
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"

    # Agent
    agent_max_iterations: int = 10
    agent_timeout_seconds: int = 120

    @property
    def data_dir(self) -> Path:
        path = Path("data")
        path.mkdir(exist_ok=True)
        return path


settings = Settings()
