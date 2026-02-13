"""
Application configuration using pydantic-settings.
All settings loaded from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal
import os


class Settings(BaseSettings):
    """Centralized application settings."""

    # --- LLM Configuration (LiteLLM) ---
    llm_provider: str = "openai"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    model_name: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    embedding_provider: str = "openai"  # openai, ollama, anthropic
    llm_timeout: int = 120  # seconds
    embedding_timeout: int = 30  # seconds
    temperature_planning: float = 0.0
    temperature_writing: float = 0.7
    max_tokens: int = 4000

    # Ollama
    enable_ollama: bool = False
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"

    # --- PostgreSQL ---
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "research_assistant"
    postgres_user: str = "research_user"
    postgres_password: str = "research_pass_2026"

    # --- MinIO ---
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_secure: bool = False
    minio_bucket_papers: str = "papers"
    minio_bucket_reports: str = "reports"

    # --- Vespa ---
    vespa_host: str = "http://vespa"
    vespa_port: int = 8080
    vespa_deploy_port: int = 19071

    # --- Data Sources ---
    arxiv_max_results: int = 20
    arxiv_delay_seconds: float = 3.0
    semantic_scholar_api_key: Optional[str] = None
    enable_semantic_scholar: bool = False
    enable_pubmed: bool = False
    enable_openalex: bool = False

    # --- Application ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    max_papers_per_query: int = 15
    top_k_papers: int = 10
    enable_caching: bool = True
    cache_ttl_hours: int = 24

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """Async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def litellm_model(self) -> str:
        """Model string for LiteLLM routing."""
        if self.llm_provider == "groq":
            return f"groq/{self.model_name.replace('groq/', '')}"
        if self.enable_ollama:
            return f"ollama/{self.ollama_model}"
        if self.llm_provider == "anthropic":
            return self.model_name
        return self.model_name

    @property
    def litellm_api_base(self) -> Optional[str]:
        """API base URL for Ollama."""
        if self.enable_ollama:
            return self.ollama_host
        return None

    @property
    def litellm_embedding_model(self) -> str:
        """Model string for LiteLLM embedding routing."""
        if self.embedding_provider == "ollama":
            return f"ollama/{self.embedding_model}"
        return self.embedding_model

    @property
    def litellm_embedding_api_base(self) -> Optional[str]:
        """API base URL for embedding provider."""
        if self.embedding_provider == "ollama":
            return self.ollama_host
        return None

    @property
    def embedding_api_base(self) -> Optional[str]:
        """API base URL for embedding provider."""
        if self.embedding_provider == "ollama":
            return self.ollama_host
        return None

    @property
    def litellm_embedding_model(self) -> str:
        """Model string for LiteLLM embedding routing."""
        if self.embedding_provider == "ollama":
            return f"ollama/{self.embedding_model}"
        return self.embedding_model


def get_settings() -> Settings:
    """Get settings instance. Creates directories on first call."""
    s = Settings()
    os.makedirs("./data/outputs/reports", exist_ok=True)
    os.makedirs("./data/outputs/pdfs", exist_ok=True)
    os.makedirs("./data/cache", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    return s


# Global settings instance
settings = get_settings()
