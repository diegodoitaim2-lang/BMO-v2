from __future__ import annotations

from copy import deepcopy
from typing import Any

from backend.core.config.paths import app_config_file, ensure_layout
from backend.core.store import load_json, save_json


def default_settings() -> dict[str, Any]:
    return {
        "app": {
            "language": "pt-BR",
            "theme": "cartoon",
            "chatFontScale": 1.0,
            "voice": {
                "enabled": True,
                "model": "pt_BR-faber-medium.onnx",
            },
            "hotkey": "Ctrl+Alt+B",
        },
        "provider": {
            "name": "openrouter",
            "model": "openai/gpt-oss-120b:free",
            "apiKey": "",
            "apiBase": "https://openrouter.ai/api/v1",
        },
        "whisper": {
            "gpu_enabled": True,
            "gpu_index": 0,
            "model": "base",
            "fallback_to_cpu": True,
        },
    }


def load_settings() -> dict[str, Any]:
    ensure_layout()
    return load_json(app_config_file(), default_settings())


def save_settings(settings: dict[str, Any]) -> dict[str, Any]:
    ensure_layout()
    current = deepcopy(default_settings())
    current.update(settings)
    save_json(app_config_file(), current)
    return current


def merge_settings(patch: dict[str, Any]) -> dict[str, Any]:
    current = load_settings()
    merged = _deep_merge(current, patch)
    save_json(app_config_file(), merged)
    return merged


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
