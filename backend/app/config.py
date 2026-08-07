"""Application settings, read from the environment (12-factor style).

Pydantic Settings validates + type-coerces the env vars once at startup. Import
`settings` anywhere; it's constructed at module import.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Load a .env from the repo root whether the process runs from the root (Docker)
    # or from backend/ (manual `uvicorn`/`alembic` in local dev), so one root .env
    # serves both. Real environment variables still take precedence over the file.
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    # Async SQLAlchemy URL (asyncpg driver). Compose sets this to the db service.
    database_url: str = "postgresql+asyncpg://rag:rag@localhost:5433/ragdb"

    # The OpenAI-compatible proxy + your personal key (see .env.example).
    openai_base_url: str = "https://llm.nat-d.uk/v1"
    openai_api_key: str = ""

    chat_model: str = "gemma-4-E4B-it"
    embed_model: str = "bge-m3"

    # bge-m3 returns 1024-dim vectors. This MUST match the vector(N) column in
    # the migration and the models. Changing the embed model? Change both.
    embed_dim: int = 1024

    # Retrieval knobs (exposed here so the whole pipeline is tunable in one place).
    top_k: int = 4                 # how many chunks to retrieve per question
    min_score: float = 0.45        # cosine-similarity floor; below this = "no match".
                                   # Tuned for bge-m3: on-topic chunks score ~0.5+,
                                   # off-topic ~0.3-0.4, so 0.45 cleanly rejects
                                   # unrelated questions. Lower it to retrieve more.
    chunk_size: int = 800          # characters per chunk
    chunk_overlap: int = 120       # characters shared between adjacent chunks

    # Sync URL for Alembic (psycopg), derived from database_url.
    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
