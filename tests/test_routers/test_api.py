"""Basic API tests."""

import pytest


@pytest.mark.asyncio
async def test_index_returns_200(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "Hermes Dashboard" in resp.text


@pytest.mark.asyncio
async def test_system_status(client):
    resp = await client.get("/api/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "cpu_percent" in data
    assert "ram_total_gb" in data
    assert data["ram_total_gb"] > 0


@pytest.mark.asyncio
async def test_sessions_list(client):
    resp = await client.get("/api/sessions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_skills_categories(client):
    resp = await client.get("/api/skills")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]


@pytest.mark.asyncio
async def test_memory_files(client):
    resp = await client.get("/api/memory")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_logs_list(client):
    resp = await client.get("/api/logs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_processes(client):
    resp = await client.get("/api/processes")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_cron_jobs(client):
    resp = await client.get("/api/cron")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_api_docs_available(client):
    resp = await client.get("/api/docs")
    assert resp.status_code == 200
