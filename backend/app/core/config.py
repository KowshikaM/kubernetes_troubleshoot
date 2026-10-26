"""Application settings, loaded from environment variables and an optional .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the backend.

    Values come from environment variables first, then from a local `.env` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "ai-kubernetes-agent"
    APP_VERSION: str = "0.1.0"

    # Networking
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"

    # InsForge Backend
    INSFORGE_URL: str = ""
    INSFORGE_API_KEY: str = ""

    # Future AI reasoning (OpenRouter)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = ""

    # Kubernetes investigation
    KUBECTL_BIN: str = "kubectl"
    KUBECTL_TIMEOUT_SECONDS: int = 30
    KUBECONFIG_PATH: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse the comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
