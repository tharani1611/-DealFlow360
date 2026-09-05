import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.core.database import engine


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client fixture for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_connections():
    """Ensure database engine connection pool is disposed between tests."""
    yield
    await engine.dispose()
