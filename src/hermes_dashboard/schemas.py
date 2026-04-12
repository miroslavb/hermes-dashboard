"""Pydantic response models for the Dashboard API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SystemStatus(BaseModel):
    cpu_percent: float
    cpu_count: int
    ram_total_gb: float
    ram_used_gb: float
    ram_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    net_sent_gb: float
    net_recv_gb: float
    uptime_seconds: float
    hostname: str
    os: str
    python_version: str
    timestamp: datetime


class SessionSummary(BaseModel):
    id: str
    started_at: str | None = None
    channel: str | None = None
    message_count: int = 0
    file_size: int = 0
    agent: str = ""


class SessionDetail(BaseModel):
    id: str
    messages: list[dict[str, Any]] = []
    agent: str = ""


class SkillCategory(BaseModel):
    name: str
    description: str = ""
    skill_count: int = 0


class SkillInfo(BaseModel):
    name: str
    category: str
    description: str = ""
    tags: list[str] = []


class MemoryFile(BaseModel):
    name: str
    size: int
    modified: float
    content: str = ""


class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    cmdline: str = ""
    create_time: float = 0


class CronJob(BaseModel):
    id: str
    name: str = ""
    schedule: str = ""
    prompt: str = ""
    status: str = "active"
    last_run: str | None = None


class LogFileInfo(BaseModel):
    name: str
    size: int
    modified: float


class LogTail(BaseModel):
    file: str
    lines: list[str]
    total_lines: int
