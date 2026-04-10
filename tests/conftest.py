"""Test fixtures for Hermes Dashboard."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["DASHBOARD_TOKEN"] = "test-token-123"

from hermes_dashboard.app import create_app


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        params={"token": "test-token-123"},
    ) as ac:
        yield ac
