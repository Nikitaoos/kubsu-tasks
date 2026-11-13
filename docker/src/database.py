import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Настройки берутся из окружения, чтобы один образ работал локально, в CI и на сервере.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://kubsu:kubsu@127.0.0.1:5432/kubsu")
SQL_ECHO = os.getenv("SQL_ECHO", "0") == "1"

engine = create_async_engine(DATABASE_URL, echo=SQL_ECHO, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
