from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


def _async_dsn(url: str) -> str:
    """Coerce a plain Postgres URL into an asyncpg-driver URL.

    Supabase / Upstash / RDS connection strings come back as
    ``postgresql://...`` which SQLAlchemy's ``create_async_engine`` rejects
    ("The asyncio extension requires an async driver to be used"). The
    asyncio engine needs an explicit driver in the scheme. SQLite already
    works with its async driver, so leave anything else untouched.
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    _async_dsn(settings.database_url),
    echo=False,
    pool_pre_ping=True,
)


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def init_db():
    import app.db.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
