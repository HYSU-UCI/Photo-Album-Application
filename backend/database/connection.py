from collections.abc import AsyncGenerator

from config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

__all__ = ["engine", "get_db"]

engine = create_async_engine(get_settings().database_url, future=True, echo=True)
AsyncSessionFactory = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
)


async def get_db() -> AsyncGenerator:
    async with AsyncSessionFactory() as session:
        yield session
