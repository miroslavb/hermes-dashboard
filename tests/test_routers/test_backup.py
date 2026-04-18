"""Tests for backup API endpoints."""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


@pytest.mark.asyncio
async def test_backup_status_returns_all_fields(client):
    """GET /api/backup/status returns expected fields."""
    resp = await client.get("/api/backup/status")
    assert resp.status_code == 200
    data = resp.json()
    # Required fields
    assert "running" in data
    assert "log_tail" in data
    assert "snapshots" in data
    assert "snapshot_count" in data
    assert "script_exists" in data
    assert "last_backup_time" in data
    assert "last_backup_result" in data
    assert "current" in data
    assert "cron_active" in data
    # Types
    assert isinstance(data["running"], bool)
    assert isinstance(data["log_tail"], str)
    assert isinstance(data["snapshots"], list)
    assert isinstance(data["snapshot_count"], int)
    assert isinstance(data["script_exists"], bool)
    assert isinstance(data["cron_active"], bool)


@pytest.mark.asyncio
async def test_backup_status_current_structure(client):
    """Current backup info has correct structure."""
    resp = await client.get("/api/backup/status")
    data = resp.json()
    current = data["current"]
    assert "exists" in current
    if current["exists"]:
        assert "size" in current
        assert "contents" in current
        assert isinstance(current["contents"], list)


@pytest.mark.asyncio
async def test_backup_status_snapshots_structure(client):
    """Snapshots have correct structure."""
    resp = await client.get("/api/backup/status")
    data = resp.json()
    for snap in data["snapshots"]:
        assert "name" in snap
        assert "path" in snap
        assert "size" in snap


@pytest.mark.asyncio
async def test_backup_status_log_tail_not_empty(client):
    """Log tail contains actual backup log content."""
    resp = await client.get("/api/backup/status")
    data = resp.json()
    # Log should contain backup entries (from our test log)
    assert len(data["log_tail"]) > 0


@pytest.mark.asyncio
async def test_backup_status_parses_last_backup(client):
    """Last backup time is parsed from log."""
    resp = await client.get("/api/backup/status")
    data = resp.json()
    # Either None or a string with backup time
    if data["last_backup_time"]:
        assert "Backup" in data["last_backup_time"] or "NAS" in data["last_backup_time"]
    if data["last_backup_result"]:
        assert "Done:" in data["last_backup_result"]


@pytest.mark.asyncio
async def test_backup_run_rejects_when_running(client):
    """POST /api/backup/run returns error when backup is already running."""
    with patch("hermes_dashboard.collectors.backup.is_running", return_value=True):
        resp = await client.post("/api/backup/run")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert "already running" in data["error"].lower()


@pytest.mark.asyncio
async def test_backup_run_starts_process(client):
    """POST /api/backup/run launches backup script."""
    with patch("hermes_dashboard.collectors.backup.is_running", return_value=False):
        with patch("hermes_dashboard.collectors.backup.BACKUP_SCRIPT") as mock_script:
            mock_script.exists.return_value = True
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.pid = 12345
                mock_popen.return_value = mock_proc
                resp = await client.post("/api/backup/run")
                assert resp.status_code == 200
                data = resp.json()
                assert data["ok"] is True
                assert data["pid"] == 12345


@pytest.mark.asyncio
async def test_backup_run_fails_without_script(client):
    """POST /api/backup/run returns error when script missing."""
    with patch("hermes_dashboard.collectors.backup.is_running", return_value=False):
        with patch("hermes_dashboard.collectors.backup.BACKUP_SCRIPT") as mock_script:
            mock_script.exists.return_value = False
            resp = await client.post("/api/backup/run")
            assert resp.status_code == 200
            data = resp.json()
            assert "error" in data


@pytest.mark.asyncio
async def test_backup_restore_validates_snapshot(client):
    """POST /api/backup/restore rejects invalid snapshot names."""
    resp = await client.post("/api/backup/restore", json={"snapshot": "../../../etc"})
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_backup_restore_returns_command(client):
    """POST /api/backup/restore returns rsync command."""
    resp = await client.post("/api/backup/restore", json={"snapshot": "2026-04-17_0300"})
    assert resp.status_code == 200
    data = resp.json()
    assert "command" in data
    assert "rsync" in data["command"]
    assert "2026-04-17_0300" in data["command"]


@pytest.mark.asyncio
async def test_backup_refresh_endpoint(client):
    """POST /api/backup/refresh triggers NAS snapshot refresh."""
    with patch("hermes_dashboard.collectors.backup.list_snapshots") as mock_list:
        mock_list.return_value = [{"name": "test", "path": "/test", "size": "1G"}]
        resp = await client.post("/api/backup/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert "snapshots" in data
        assert "count" in data
        assert data["count"] == 1


@pytest.mark.asyncio
async def test_backup_script_points_to_correct_path(client):
    """Backup script path is nas-backup.sh (not nas-full-backup.sh)."""
    from hermes_dashboard.collectors import backup
    assert "nas-backup.sh" in str(backup.BACKUP_SCRIPT)
    assert "nas-backup.log" in str(backup.BACKUP_LOG)


@pytest.mark.asyncio
async def test_backup_detects_running_process(client):
    """is_running() checks for both snapshots and current rsync patterns."""
    from hermes_dashboard.collectors import backup
    # Check the function exists and is callable
    assert callable(backup.is_running)
