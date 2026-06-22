from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

from backend.core.agent.runtime import AgentRuntime
from backend.core.config.paths import (
    app_home,
    history_file,
    logs_file,
    memory_dir,
    project_root,
    runtime_dir,
    skills_dir,
    subagents_file,
    tasks_file,
    voices_dir,
    workspace_dir,
)
from backend.core.config.settings import load_settings
from backend.core.store import load_json, tail_lines


VOICE_DEFS = [
    ("bmo.onnx", "BMO", "pt-BR"),
    ("pt_BR-faber-medium.onnx", "Portugues BR - Faber", "pt-BR"),
    ("pt-BR-razo-medium.onnx", "Portugues BR - Razo", "pt-BR"),
    ("miro_pt-BR.onnx", "Miro PT-BR", "pt-BR"),
    ("pt_BR-sage_13364-medium.onnx", "Sage PT-BR", "pt-BR"),
    ("dii_pt-BR.onnx", "Dii PT-BR", "pt-BR"),
    ("en_GB-semaine-medium.onnx", "English GB - Semaine", "en-GB"),
]

CHANNEL_LABELS = {
    "dingtalk": "DingTalk",
    "discord": "Discord",
    "email": "Email",
    "feishu": "Feishu",
    "matrix": "Matrix",
    "mochat": "Mochat",
    "msteams": "Microsoft Teams",
    "napcat": "Napcat",
    "qq": "QQ",
    "signal": "Signal",
    "slack": "Slack",
    "telegram": "Telegram",
    "websocket": "WebSocket",
    "wecom": "WeCom",
    "weixin": "Weixin",
    "whatsapp": "WhatsApp",
}

TOOL_DEFS = [
    {"name": "Web Search", "category": "Web", "description": "Pesquisa na internet."},
    {"name": "Web Fetch", "category": "Web", "description": "Le o conteudo de uma pagina web."},
    {"name": "Read File", "category": "Arquivos", "description": "Le arquivos do workspace."},
    {"name": "Write File", "category": "Arquivos", "description": "Cria ou sobrescreve arquivos."},
    {"name": "Edit File", "category": "Arquivos", "description": "Edita trechos de arquivos."},
    {"name": "Apply Patch", "category": "Arquivos", "description": "Aplica patches no codigo."},
    {"name": "Find Files", "category": "Arquivos", "description": "Busca arquivos por nome."},
    {"name": "Grep", "category": "Arquivos", "description": "Busca texto dentro de arquivos."},
    {"name": "List Dir", "category": "Arquivos", "description": "Lista pastas."},
    {"name": "Exec", "category": "Execucao", "description": "Executa comandos no terminal."},
    {"name": "Shell", "category": "Execucao", "description": "Executa scripts shell."},
    {"name": "Run CLI App", "category": "Execucao", "description": "Executa apps de linha de comando."},
    {"name": "Cron", "category": "Tarefas", "description": "Agenda tarefas futuras."},
    {"name": "Long Task", "category": "Tarefas", "description": "Executa tarefas longas em background."},
    {"name": "Message", "category": "Agente", "description": "Envia mensagens pelos canais."},
    {"name": "Spawn", "category": "Agente", "description": "Cria subagentes."},
    {"name": "Complete Goal", "category": "Meta", "description": "Marca objetivos como concluidos."},
    {"name": "My", "category": "Agente", "description": "Informa sobre o proprio BMO."},
]


def _runtime_file_exists(relative: str) -> bool:
    return (runtime_dir() / relative).exists()


def list_voice_models() -> list[dict[str, Any]]:
    voices = []
    for filename, label, language in VOICE_DEFS:
        path = runtime_dir() / "piper" / filename
        if not path.exists():
            path = voices_dir() / filename
        voices.append({
            "file": filename,
            "label": label,
            "language": language,
            "path": str(path),
            "exists": path.exists(),
        })
    return voices


def list_channels() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    internal = {"base", "manager", "registry"}
    try:
        channels_pkg = importlib.import_module("nanobot.channels")
        for module in pkgutil.iter_modules(channels_pkg.__path__):
            if module.name.startswith("_") or module.name in internal:
                continue
            items.append({
                "id": module.name,
                "label": CHANNEL_LABELS.get(module.name, module.name.replace("_", " ").title()),
                "enabled": False,
                "configured": False,
                "status": "disponivel",
            })
    except Exception:
        for module_name in [
            "telegram", "discord", "slack", "whatsapp", "email", "matrix", "signal",
            "websocket", "dingtalk", "feishu", "qq", "msteams", "wecom", "weixin", "mochat",
        ]:
            items.append({
                "id": module_name,
                "label": CHANNEL_LABELS.get(module_name, module_name.replace("_", " ").title()),
                "enabled": False,
                "configured": False,
                "status": "disponivel",
            })
    return sorted(items, key=lambda item: item["id"])


def list_skills() -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    roots = [project_root() / "nanobot" / "skills", skills_dir()]
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for skill_file in root.glob("*/SKILL.md"):
            skill_id = skill_file.parent.name
            if skill_id in seen:
                continue
            seen.add(skill_id)
            lines = skill_file.read_text(encoding="utf-8", errors="replace").splitlines()
            first_line = next((line.strip() for line in lines if line.strip() and line.strip() != "---"), "")
            if first_line.startswith("#"):
                first_line = first_line.lstrip("# ").strip()
            skills.append({
                "id": skill_id,
                "name": skill_id,
                "description": first_line,
                "path": str(skill_file),
                "scope": "builtin" if root != skills_dir() else "workspace",
            })
    return sorted(skills, key=lambda item: item["name"].lower())


def list_workspace_items(limit: int = 200) -> list[dict[str, Any]]:
    root = workspace_dir()
    if not root.exists():
        return []
    items: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if len(items) >= limit:
            break
        stat = path.stat()
        items.append({
            "name": path.name,
            "path": str(path),
            "is_dir": path.is_dir(),
            "size": 0 if path.is_dir() else stat.st_size,
            "modified": int(stat.st_mtime),
            "category": "pasta" if path.is_dir() else "arquivo",
        })
    return items


def list_memory_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    soul = project_root() / "SOUL.md"
    if soul.exists():
        items.append({"id": "soul", "text": soul.read_text(encoding="utf-8", errors="replace"), "source": str(soul)})
    memory = memory_dir() / "MEMORY.md"
    if memory.exists():
        items.append({"id": "memory", "text": memory.read_text(encoding="utf-8", errors="replace"), "source": str(memory)})
    user = memory_dir() / "USER.md"
    if user.exists():
        items.append({"id": "user", "text": user.read_text(encoding="utf-8", errors="replace"), "source": str(user)})
    stored = load_json(memory_dir() / "memory.json", [])
    if isinstance(stored, list):
        for index, entry in enumerate(stored):
            if not isinstance(entry, dict):
                continue
            items.append({
                "id": str(entry.get("id") or f"item-{index}"),
                "text": str(entry.get("text") or ""),
                "source": str(entry.get("source") or "memory.json"),
            })
    return items


def list_history_sessions() -> list[dict[str, Any]]:
    payload = load_json(history_file(), {"sessions": []})
    sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
    if not isinstance(sessions, list):
        return []
    return sessions


def list_reminders() -> list[dict[str, Any]]:
    payload = load_json(app_home() / "reminders" / "reminders.json", {"items": []})
    items = payload.get("items", []) if isinstance(payload, dict) else []
    return items if isinstance(items, list) else []


def list_subagents() -> list[dict[str, Any]]:
    payload = load_json(subagents_file(), {"items": []})
    items = payload.get("items", []) if isinstance(payload, dict) else []
    return items if isinstance(items, list) else []


def list_tasks() -> list[dict[str, Any]]:
    payload = load_json(tasks_file(), {"items": []})
    items = payload.get("items", []) if isinstance(payload, dict) else []
    return items if isinstance(items, list) else []


def build_bootstrap(runtime: AgentRuntime) -> dict[str, Any]:
    settings = load_settings()
    voices = list_voice_models()
    channels = list_channels()
    skills = list_skills()
    memory = list_memory_items()
    history = list_history_sessions()
    reminders = list_reminders()
    subagents = list_subagents()
    tasks = list_tasks()
    logs = tail_lines(logs_file(), 80)
    return {
        "settings": settings,
        "system": build_system_snapshot(runtime, voices=voices, channels=channels, skills=skills, memory=memory, history=history),
        "voices": {"voices": voices, "selected": settings.get("app", {}).get("voice", {}).get("model")},
        "channels": {"channels": channels},
        "skills": {"skills": skills},
        "memory": {"items": memory},
        "history": {"sessions": history},
        "reminders": {"items": reminders},
        "subagents": {"items": subagents, "busy": False},
        "tasks": {"items": tasks},
        "tools": {"tools": TOOL_DEFS, "runtimeTools": runtime.tool_names},
        "workspace": {"path": str(workspace_dir()), "items": list_workspace_items()},
        "logs": {"lines": logs},
    }


def build_system_snapshot(
    runtime: AgentRuntime,
    *,
    voices: list[dict[str, Any]] | None = None,
    channels: list[dict[str, Any]] | None = None,
    skills: list[dict[str, Any]] | None = None,
    memory: list[dict[str, Any]] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    voices = voices if voices is not None else list_voice_models()
    channels = channels if channels is not None else list_channels()
    skills = skills if skills is not None else list_skills()
    memory = memory if memory is not None else list_memory_items()
    history = history if history is not None else list_history_sessions()
    settings = load_settings()
    runtime_status = runtime.status()
    piper_exe = runtime_dir() / "piper" / "piper" / "piper.exe"
    whisper_exe = runtime_dir() / "whisper.cpp" / "Win32" / "Release" / "whisper-cli.exe"
    wakeword_model = runtime_dir() / "wakeword.onnx"
    whisper_model = runtime_dir() / "whisper.cpp" / "models" / "ggml-base.bin"
    return {
        "backend": True,
        "piper": piper_exe.exists() and any(voice.get("exists") for voice in voices),
        "whisper": whisper_exe.exists() and whisper_model.exists(),
        "wakeword": {
            "enabled": wakeword_model.exists(),
            "available": wakeword_model.exists(),
            "dependency": wakeword_model.exists(),
            "running": False,
            "eventId": 0,
            "model": str(wakeword_model),
            "message": "Wake word pronto" if wakeword_model.exists() else "Aguardando wakeword.onnx",
        },
        "runtime": {
            "ready": runtime_status.ready,
            "error": runtime_status.error,
            "toolCount": runtime_status.tool_count,
            "provider": runtime_status.provider,
            "model": runtime_status.model,
        },
        "diagnostic": {
            "provider": {
                "ok": bool(settings.get("provider", {}).get("apiKey")),
                "name": settings.get("provider", {}).get("name", "openrouter"),
                "model": settings.get("provider", {}).get("model", ""),
            },
            "voices": {"ok": any(voice.get("exists") for voice in voices), "count": len(voices)},
            "memory": {"ok": bool(memory), "path": str(memory_dir())},
            "history": {"ok": bool(history), "count": len(history)},
            "skills": {"ok": bool(skills), "count": len(skills)},
            "channels": {"ok": bool(channels), "items": channels},
            "workspace": {"ok": True, "path": str(workspace_dir())},
        },
        "provider": {
            "ok": bool(settings.get("provider", {}).get("apiKey")),
            "name": settings.get("provider", {}).get("name", "openrouter"),
            "model": settings.get("provider", {}).get("model", ""),
        },
        "voice": {
            "enabled": settings.get("app", {}).get("voice", {}).get("enabled", True),
            "model": settings.get("app", {}).get("voice", {}).get("model", "pt_BR-faber-medium.onnx"),
            "models": voices,
        },
        "settings": settings,
        "summary": {
            "memory": len(memory),
            "history": len(history),
            "skills": len(skills),
            "channels": len(channels),
            "tools": len(TOOL_DEFS),
        },
    }
