"""Async SQLAlchemy setup - engine, session factory, declarative Base, and
the FastAPI dependency used to get a DB session per request."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    """FastAPI dependency - yields a DB session, closes it after the request."""
    async with AsyncSessionLocal() as session:
        yield session