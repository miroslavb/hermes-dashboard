"""Test fixtures for Hermes Dashboard."""

import pytest
from httpx import ASGITransport, AsyncClient

from hermes_dashboard.app import create_app


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
