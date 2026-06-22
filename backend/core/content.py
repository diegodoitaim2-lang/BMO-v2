from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.core.config.paths import history_file, memory_file, skills_dir
from backend.core.store import load_json, save_json


def _ensure_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    items: list[dict[str, Any]] = []
    for entry in value:
        if isinstance(entry, dict):
            items.append(entry)
    return items


def _now_stamp() -> int:
    return int(time.time())


def _now_label() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")


def _slugify(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or fallback


def _role_label(role: str) -> str:
    normalized = role.strip().lower()
    if normalized in {"assistant", "bmo", "bot"}:
        return "BMO"
    if normalized == "system":
        return "Sistema"
    return "Usuário" if normalized == "user" else role.title()


def read_memory_records() -> list[dict[str, Any]]:
    payload = load_json(memory_file(), [])
    return _ensure_list(payload)


def write_memory_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = _ensure_list(items)
    save_json(memory_file(), records)
    return records


def add_memory_record(text: str, *, source: str = "manual") -> tuple[dict[str, Any], list[dict[str, Any]]]:
    body = text.strip()
    if not body:
        raise ValueError("Memoria vazia nao pode ser salva.")
    records = read_memory_records()
    item = {
        "id": f"memory-{_now_stamp()}-{_slugify(body[:24])}",
        "text": body,
        "source": source,
        "createdAt": _now_stamp(),
    }
    records.insert(0, item)
    write_memory_records(records)
    return item, records


def delete_memory_record(record_id: str) -> list[dict[str, Any]]:
    records = [item for item in read_memory_records() if str(item.get("id")) != str(record_id)]
    return write_memory_records(records)


def clear_memory_records() -> list[dict[str, Any]]:
    return write_memory_records([])


def export_memory_payload() -> dict[str, Any]:
    records = read_memory_records()
    filename = f"BMO_memoria_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    content = json.dumps(
        {"exportedAt": _now_label(), "items": records},
        ensure_ascii=False,
        indent=2,
    )
    return {
        "ok": True,
        "filename": filename,
        "content": content,
        "mime": "application/json",
        "format": "json",
        "count": len(records),
    }


def read_history_sessions() -> list[dict[str, Any]]:
    payload = load_json(history_file(), {"sessions": []})
    sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
    return _ensure_list(sessions)


def write_history_sessions(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = _ensure_list(sessions)
    save_json(history_file(), {"sessions": records})
    return records


def delete_history_session(session_id: str) -> list[dict[str, Any]]:
    sessions = [item for item in read_history_sessions() if str(item.get("id")) != str(session_id)]
    return write_history_sessions(sessions)


def clear_history_sessions() -> list[dict[str, Any]]:
    return write_history_sessions([])


def _render_session_text(session: dict[str, Any], *, markdown: bool) -> str:
    title = str(session.get("title") or session.get("id") or "Conversa")
    created = session.get("createdAt")
    updated = session.get("updatedAt")
    messages = session.get("messages", [])
    lines: list[str] = []
    if markdown:
        lines.append(f"# {title}")
        if session.get("id"):
            lines.append(f"- ID: {session.get('id')}")
        if created:
            lines.append(f"- Criado em: {created}")
        if updated:
            lines.append(f"- Atualizado em: {updated}")
        lines.append("")
    else:
        lines.append(title)
        if session.get("id"):
            lines.append(f"ID: {session.get('id')}")
        if created:
            lines.append(f"Criado em: {created}")
        if updated:
            lines.append(f"Atualizado em: {updated}")
        lines.append("")

    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = _role_label(str(message.get("role") or "user"))
            text = str(message.get("text") or "").strip()
            if not text:
                continue
            if markdown:
                lines.append(f"## {role}")
                lines.append(text)
                lines.append("")
            else:
                lines.append(f"{role}: {text}")

    return "\n".join(lines).strip()


def export_history_payload(session_id: str | None, fmt: str) -> dict[str, Any]:
    sessions = read_history_sessions()
    selected = sessions
    if session_id:
        selected = [item for item in sessions if str(item.get("id")) == str(session_id)]
    if session_id and not selected:
        raise ValueError("Sessao de historico nao encontrada.")

    fmt_normalized = (fmt or "json").lower()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    base = "BMO_historico" if not session_id else f"BMO_historico_{_slugify(session_id)}"

    if fmt_normalized == "md":
        content = "\n\n---\n\n".join(_render_session_text(session, markdown=True) for session in selected) or "# Historico\n\nSem conversas."
        return {
            "ok": True,
            "filename": f"{base}_{stamp}.md",
            "content": content,
            "mime": "text/markdown",
            "format": "md",
            "count": len(selected),
        }

    if fmt_normalized == "txt":
        content = "\n\n====\n\n".join(_render_session_text(session, markdown=False) for session in selected) or "Historico vazio."
        return {
            "ok": True,
            "filename": f"{base}_{stamp}.txt",
            "content": content,
            "mime": "text/plain",
            "format": "txt",
            "count": len(selected),
        }

    content = json.dumps(
        {"exportedAt": _now_label(), "sessions": selected},
        ensure_ascii=False,
        indent=2,
    )
    return {
        "ok": True,
        "filename": f"{base}_{stamp}.json",
        "content": content,
        "mime": "application/json",
        "format": "json",
        "count": len(selected),
    }


def create_skill_scaffold(name: str, description: str = "") -> dict[str, Any]:
    skill_name = name.strip()
    if not skill_name:
        raise ValueError("Informe um nome para a skill.")

    slug = _slugify(skill_name)
    folder = skills_dir() / slug
    skill_file = folder / "SKILL.md"
    if skill_file.exists():
        raise FileExistsError(f"Skill '{skill_name}' ja existe.")

    folder.mkdir(parents=True, exist_ok=True)
    summary = description.strip() or "Descreva aqui quando o BMO deve usar esta skill."
    content = (
        f"# {skill_name}\n\n"
        "## Quando usar\n"
        f"{summary}\n\n"
        "## Passos sugeridos\n"
        "- Explique o objetivo em uma frase.\n"
        "- Liste os passos principais.\n"
        "- Inclua exemplos curtos se fizer sentido.\n"
    )
    skill_file.write_text(content, encoding="utf-8")
    return {
        "id": slug,
        "name": skill_name,
        "description": summary,
        "path": str(skill_file),
        "scope": "workspace",
    }
