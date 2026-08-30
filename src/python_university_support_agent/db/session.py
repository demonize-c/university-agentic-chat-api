from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from ..config import settings


DATABASE_URL = (
    f"mysql+aiomysql://"
    f"{settings.database_user}:{settings.database_password}"
    f"@{settings.database_host}:{settings.database_port}"
    f"/{settings.database_name}"
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
SessionLocal = AsyncSessionLocal  # backward compatibility alias
sessionLocal = AsyncSessionLocal  # backward compatibility alias
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db

