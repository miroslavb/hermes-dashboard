"""Backup collector — status, snapshots, run, restore."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

BACKUP_SCRIPT = Path("/root/.hermes/scripts/nas-backup.sh")
BACKUP_LOG = Path("/root/.hermes/logs/nas-backup.log")
NAS_IP = "100.97.192.84"
NAS_USER = "bereft"
NAS_PASS = "Nhmft1378"
NAS_BASE = "/volume1/Backups/hermes"
SNAP_BASE = f"{NAS_BASE}/snapshots"
CURRENT_DIR = f"{NAS_BASE}/current"

_SSH_OPTS = "-o StrictHostKeyChecking=no -o ConnectTimeout=5"


def _ssh_cmd(remote_cmd: str) -> str:
    return (
        f"sshpass -p '{NAS_PASS}' ssh {_SSH_OPTS} "
        f"{NAS_USER}@{NAS_IP} '{remote_cmd}'"
    )


def is_running() -> bool:
    """Check if rsync backup is currently running."""
    try:
        out = subprocess.check_output(
            ["pgrep", "-f", "rsync.*(snapshots|current)"], text=True, timeout=5
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
                shell=True, text=True, timeout=5,
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


def get_current_backup() -> dict:
    """Get info about the current backup on NAS. Uses cache to avoid slow SSH."""
    cache = Path("/root/.hermes/logs/nas-current-size.txt")
    if cache.exists():
        size = cache.read_text().strip()
        return {"exists": True, "size": size, "contents": ["root", "etc", "tmp"]}
    return {"exists": False}


def get_cron_active() -> bool:
    """Check if backup cron job is configured."""
    try:
        out = subprocess.check_output("crontab -l 2>/dev/null", shell=True, text=True, timeout=5).strip()
        return "nas-backup" in out
    except Exception:
        return False


def get_status() -> dict:
    """Full backup status. Avoids SSH calls — uses cache for NAS data."""
    running = is_running()
    log_tail = get_log_tail()
    # Use cache only — SSH to NAS is too slow for dashboard
    snapshots = list_snapshots(refresh=False)
    current = get_current_backup()

    # Parse last backup time and result from log
    last_backup_time = None
    last_backup_result = None
    if BACKUP_LOG.exists():
        lines = BACKUP_LOG.read_text(encoding="utf-8", errors="replace").split("\n")
        for line in reversed(lines):
            if "Done:" in line and "ok" in line:
                last_backup_result = line.strip()
                break
        for line in reversed(lines):
            if line.strip().startswith("=== ") and "Backup" in line:
                last_backup_time = line.strip().strip("=").strip()
                break

    return {
        "running": running,
        "log_tail": log_tail,
        "last_backup_time": last_backup_time,
        "last_backup_result": last_backup_result,
        "current": current,
        "snapshots": snapshots,
        "snapshot_count": len(snapshots),
        "script_exists": BACKUP_SCRIPT.exists(),
        "cron_active": get_cron_active(),
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
