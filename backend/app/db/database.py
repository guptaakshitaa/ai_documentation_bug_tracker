"""
Async SQLAlchemy setup. Defaults to a local SQLite file (assistant.db) so the
app runs with zero external setup. Point DATABASE_URL at a Postgres instance
(e.g. postgresql+asyncpg://user:pass@host/db) for production without
changing any model or query code.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create tables if they don't exist yet. Called once on app startup."""
    from app.db import models  # noqa: F401  (ensures models are registered on Base)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncSession:
    """FastAPI dependency: yields a session, closes it after the request."""
    async with AsyncSessionLocal() as session:
        yield session
