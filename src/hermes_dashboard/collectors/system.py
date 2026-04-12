"""System metrics collector using psutil."""

from __future__ import annotations

import platform
import time
from datetime import datetime

import psutil

from hermes_dashboard.schemas import SystemStatus

_boot_time = psutil.boot_time()


def collect_system_status() -> SystemStatus:
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    return SystemStatus(
        cpu_percent=psutil.cpu_percent(interval=0.1),
        cpu_count=psutil.cpu_count(),
        ram_total_gb=round(mem.total / 1e9, 2),
        ram_used_gb=round(mem.used / 1e9, 2),
        ram_percent=mem.percent,
        disk_total_gb=round(disk.total / 1e9, 2),
        disk_used_gb=round(disk.used / 1e9, 2),
        disk_percent=disk.percent,
        net_sent_gb=round(net.bytes_sent / 1e9, 2),
        net_recv_gb=round(net.bytes_recv / 1e9, 2),
        uptime_seconds=round(time.time() - _boot_time, 1),
        hostname=platform.node(),
        os=f"{platform.system()} {platform.release()}",
        python_version=platform.python_version(),
        timestamp=datetime.now(),
    )
