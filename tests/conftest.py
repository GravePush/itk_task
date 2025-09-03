
import json

from asyncio import get_running_loop
import logging
import asyncpg
import pytest_asyncio
from alembic import command
from alembic.config import Config
from pytest import fixture
from httpx import AsyncClient, ASGITransport
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from api.models import WalletModel
from config import POSTGRES_USER, POSTGRES_PASSWORD, DB_HOST, DB_PORT, POSTGRES_DB
from database import async_session_maker, get_db
from main import app

logger = logging.getLogger("tests")
TEST_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"


@fixture(scope="session", autouse=True)
async def prepare_db():
    conn = await asyncpg.connect(
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database="postgres"
    )
    await conn.execute(f'DROP DATABASE IF EXISTS "{POSTGRES_DB}"')
    await conn.execute(f'CREATE DATABASE "{POSTGRES_DB}"')
    logger.info(f"Database {POSTGRES_DB} was created!")
    await conn.close()

    loop = get_running_loop()
    alembic_config = Config("alembic.ini")
    await loop.run_in_executor(None, command.upgrade, alembic_config, "head")
    logger.info("Migrations successfully applied")

    def open_mock_json(model: str):
        with open(f"tests/mock_data_{model}.json", encoding="utf-8") as file:
            return json.load(file)

    wallets = open_mock_json("wallets")

    async with async_session_maker() as session:
        add_wallets = insert(WalletModel).values(wallets)
        await session.execute(add_wallets)
        await session.commit()


@pytest_asyncio.fixture(scope="function")
async def session():
    engine = create_async_engine(TEST_DATABASE_URL, pool_size=5, max_overflow=10)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def session_for_concurrent_withdraw():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_size=5, max_overflow=10)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return async_session


@pytest_asyncio.fixture(scope="function")
async def ac(session):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_db] = override_get_session

    async with AsyncClient(
            base_url="http://test",
            transport=ASGITransport(app=app)
    ) as client:
        yield client
