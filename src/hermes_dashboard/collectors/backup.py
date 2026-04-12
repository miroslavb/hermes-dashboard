"""Backup collector — status, snapshots, run, restore."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

BACKUP_SCRIPT = Path("/root/.hermes/scripts/nas-full-backup.sh")
BACKUP_LOG = Path("/root/.hermes/logs/nas-full-backup.log")
NAS_IP = "100.97.192.84"
NAS_USER = "bereft"
NAS_PASS = "Nhmft1378"
SNAP_BASE = "/volume1/Backups/hermes/snapshots"

_SSH_OPTS = "-o StrictHostKeyChecking=no -o ConnectTimeout=10"


def _ssh_cmd(remote_cmd: str) -> str:
    return (
        f"sshpass -p '{NAS_PASS}' ssh {_SSH_OPTS} "
        f"{NAS_USER}@{NAS_IP} '{remote_cmd}'"
    )


def is_running() -> bool:
    """Check if rsync backup is currently running."""
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", "rsync.*snapshots"], text=True, timeout=5
        ).strip()
        return bool(out)
    except subprocess.CalledProcessError:
        return False


def get_log_tail(lines: int = 80) -> str:
    """Return last N lines of backup log."""
    if not BACKUP_LOG.exists():
        return ""
    all_lines = BACKUP_LOG.read_text(encoding="utf-8", errors="replace").split("\n")
    return "\n".join(all_lines[-lines:])


SNAP_CACHE = Path("/root/.hermes/logs/nas-snapshots-cache.json")


def list_snapshots(refresh: bool = False) -> list[dict]:
    """List snapshots on NAS. Uses local cache to avoid SSH timeout during backup."""
    # Return cached if not refreshing
    if not refresh:
        if SNAP_CACHE.exists():
            try:
                return json.loads(SNAP_CACHE.read_text()).get("snapshots", [])
            except Exception:
                pass
        return []

    # Refresh from NAS
    try:
        raw = subprocess.check_output(
            _ssh_cmd(f"ls -1d {SNAP_BASE}/20* 2>/dev/null || true"),
            shell=True, text=True, timeout=8,
        ).strip()
    except Exception:
        # Return stale cache if available
        if SNAP_CACHE.exists():
            try:
                return json.loads(SNAP_CACHE.read_text()).get("snapshots", [])
            except Exception:
                pass
        return []

    if not raw:
        return []

    snapshots = []
    for snap_path in raw.split("\n"):
        snap_path = snap_path.strip()
        if not snap_path:
            continue
        name = snap_path.rsplit("/", 1)[-1]
        try:
            size_raw = subprocess.check_output(
                _ssh_cmd(f"du -sh {snap_path} 2>/dev/null | cut -f1"),
                shell=True, text=True, timeout=8,
            ).strip()
        except Exception:
            size_raw = "?"
        snapshots.append({"name": name, "path": snap_path, "size": size_raw})

    # Update cache
    try:
        SNAP_CACHE.write_text(json.dumps({"ts": time.time(), "snapshots": snapshots}))
    except Exception:
        pass

    return snapshots


def get_status() -> dict:
    """Full backup status. Avoids SSH when backup is running."""
    running = is_running()
    log_tail = get_log_tail()
    # Skip SSH when backup is running — use cache only
    snapshots = list_snapshots(refresh=not running)

    return {
        "running": running,
        "log_tail": log_tail,
        "snapshots": snapshots,
        "snapshot_count": len(snapshots),
        "script_exists": BACKUP_SCRIPT.exists(),
    }


def run_backup() -> dict:
    """Launch backup script in background."""
    if not BACKUP_SCRIPT.exists():
        return {"error": "Backup script not found"}

    if is_running():
        return {"error": "Backup already running"}

    proc = subprocess.Popen(
        ["bash", str(BACKUP_SCRIPT)],
        stdout=open(BACKUP_LOG, "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    return {"ok": True, "pid": proc.pid}


def get_restore_command(snapshot: str, target: str = "/") -> dict:
    """Generate restore rsync command for a snapshot."""
    if not snapshot or ".." in snapshot or "/" in snapshot:
        return {"error": "Invalid snapshot name"}

    snap_path = f"{SNAP_BASE}/{snapshot}"
    cmd = (
        f"sshpass -p '{NAS_PASS}' rsync -avz "
        f"-e 'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30' "
        f"--exclude=/proc --exclude=/sys --exclude=/dev --exclude=/tmp --exclude=/run "
        f"{NAS_USER}@{NAS_IP}:{snap_path}/ {target}/"
    )
    return {
        "command": cmd,
        "warning": "This will overwrite local files. Run manually to confirm.",
        "snapshot": snapshot,
        "target": target,
    }
