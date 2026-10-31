"""Pytest configuration and fixtures for testing."""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database.connection import init_db
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    """Ensure database tables are initialized before tests execute."""
    await init_db()


@pytest_asyncio.fixture(scope="function")
async def client():
    """Async HTTP client for testing API endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
