"""Application configuration."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ai_provider: Literal["azure_openai", "openai", "ollama"] = "azure_openai"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # Azure OpenAI settings
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    # Template fallback toggle
    template_fallback: bool = False

    # Database connection URL (SQLite or Postgres)
    database_url: str = "sqlite:///./data/asac.db"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    agent_timeout: int = 60
    pipeline_timeout: int = 180
    max_tokens: int = 950

    rag_top_k: int = 5
    knowledge_dir: str = "knowledge"

    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def knowledge_path(self) -> Path:
        backend_root = Path(__file__).resolve().parent.parent.parent
        kb_path = backend_root / self.knowledge_dir
        if not kb_path.exists():
            kb_path = backend_root / "backend" / self.knowledge_dir
        return kb_path


settings = Settings()

