"""
Central configuration for the AI Documentation & Bug Resolution Assistant backend.

Reads settings from environment variables (see .env.example). When no GitHub
token or LLM API key is provided, the app still runs:
  - GitHub calls fall back to unauthenticated requests (60 requests/hour limit).
  - AI/LLM calls fall back to mocked responses (see app/services/ai_mock.py).
"""
import os
from functools import lru_cache


class Settings:
    # GitHub
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    github_api_base: str = "https://api.github.com"

    # LLM (OpenAI-compatible). Left unset -> mock mode.
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Database. Defaults to a local SQLite file; swap for a Postgres URL in
    # production, e.g. postgresql+asyncpg://user:pass@host/dbname
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./assistant.db")

    # App
    app_name: str = "AI Documentation & Bug Resolution Assistant"
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

    @property
    def github_configured(self) -> bool:
        return bool(self.github_token)

    @property
    def llm_configured(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
