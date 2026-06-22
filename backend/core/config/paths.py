from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def app_home() -> Path:
    base = os.environ.get("BMO_HOME")
    if base:
        return Path(base).expanduser()
    return Path.home() / ".bmo-v2"


def config_dir() -> Path:
    return app_home() / "config"


def data_dir() -> Path:
    return app_home() / "data"


def logs_dir() -> Path:
    return app_home() / "logs"


def memory_dir() -> Path:
    return app_home() / "memory"


def history_dir() -> Path:
    return app_home() / "history"


def workspace_dir() -> Path:
    return app_home() / "workspace"


def skills_dir() -> Path:
    return workspace_dir() / "skills"


def reminders_dir() -> Path:
    return app_home() / "reminders"


def subagents_dir() -> Path:
    return app_home() / "sessions"


def voices_dir() -> Path:
    return app_home() / "voices"


def runtime_dir() -> Path:
    return project_root() / "runtime"


def app_config_file() -> Path:
    return config_dir() / "settings.json"


def history_file() -> Path:
    return history_dir() / "history.json"


def memory_file() -> Path:
    return memory_dir() / "memory.json"


def reminders_file() -> Path:
    return reminders_dir() / "reminders.json"


def subagents_file() -> Path:
    return subagents_dir() / "subagents.json"


def tasks_file() -> Path:
    return subagents_dir() / "tasks.json"


def logs_file() -> Path:
    return logs_dir() / "bmo.log"


def ensure_layout() -> None:
    for folder in [
        config_dir(),
        data_dir(),
        logs_dir(),
        memory_dir(),
        history_dir(),
        workspace_dir(),
        skills_dir(),
        reminders_dir(),
        subagents_dir(),
        voices_dir(),
    ]:
        folder.mkdir(parents=True, exist_ok=True)
