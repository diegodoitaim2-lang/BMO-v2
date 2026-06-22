from __future__ import annotations

from dataclasses import asdict
from typing import Any, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.core.agent.runtime import AgentRuntime
from backend.core.content import (
    add_memory_record,
    clear_memory_records,
    create_skill_scaffold,
    delete_memory_record,
    export_memory_payload,
    read_memory_records,
)
from backend.core.bootstrap import (
    build_bootstrap,
    build_system_snapshot,
    list_channels,
    list_memory_items,
    list_skills,
    list_tasks,
    list_voice_models,
    list_workspace_items,
)
from backend.core.config.paths import ensure_layout, logs_file, workspace_dir
from backend.core.config.settings import load_settings, merge_settings
from backend.core.voice import piper_ready, speak_text, test_whisper_runtime, whisper_status
from backend.core.store import tail_lines
from nanobot.providers.registry import PROVIDERS


app = FastAPI(title="BMO-V2 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:4173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

runtime = AgentRuntime()


class ChatPayload(BaseModel):
    message: str = Field(min_length=1)
    sessionId: str | None = None
    language: str = "pt-BR"


class SettingsPayload(BaseModel):
    app: dict[str, Any] | None = None
    provider: dict[str, Any] | None = None
    whisper: dict[str, Any] | None = None


class ProviderTestPayload(BaseModel):
    provider: str | None = None
    model: str | None = None
    apiKey: str | None = None


class SpeakPayload(BaseModel):
    text: str
    voice: str | None = None


class WhisperTestPayload(BaseModel):
    model: str | None = None


class MemoryPayload(BaseModel):
    action: Literal["add", "delete", "clear", "export"] = "export"
    id: str | None = None
    text: str | None = None


class HistoryPayload(BaseModel):
    action: Literal["delete", "clear"] = "delete"
    id: str | None = None


class HistoryExportPayload(BaseModel):
    sessionId: str | None = None
    format: Literal["json", "txt", "md"] = "json"


class SkillCreatePayload(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""


class ReminderPayload(BaseModel):
    action: Literal["add", "remove", "clear"] = "add"
    id: str | None = None
    text: str | None = None
    name: str | None = None
    afterMinutes: int | None = Field(default=None, ge=1)
    at: str | None = None
    everySeconds: int | None = Field(default=None, ge=1)
    cronExpr: str | None = None
    tz: str | None = None
    deliver: bool = True


class SubagentPayload(BaseModel):
    action: Literal["spawn", "cancel"] = "spawn"
    task: str | None = None
    title: str | None = None
    sessionKey: str | None = None


@app.on_event("startup")
def _startup() -> None:
    ensure_layout()
    runtime.ensure_ready()


@app.on_event("shutdown")
def _shutdown() -> None:
    runtime.shutdown()


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "name": "BMO-V2", "runtime": asdict(runtime.status())}


@app.get("/api/bootstrap")
def bootstrap() -> dict[str, Any]:
    return build_bootstrap(runtime)


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    return load_settings()


@app.post("/api/settings")
def post_settings(payload: SettingsPayload) -> dict[str, Any]:
    current = load_settings()
    patch: dict[str, Any] = {}
    if payload.app is not None:
        patch["app"] = payload.app
    if payload.provider is not None:
        patch["provider"] = payload.provider
    if payload.whisper is not None:
        patch["whisper"] = payload.whisper
    merged = merge_settings(patch) if patch else current
    runtime.reload()
    runtime.ensure_ready()
    return merged


@app.get("/api/system")
def system() -> dict[str, Any]:
    return build_system_snapshot(runtime)


@app.get("/api/voices")
def voices() -> dict[str, Any]:
    settings = load_settings()
    models = list_voice_models()
    return {
        "voices": models,
        "selected": settings.get("app", {}).get("voice", {}).get("model"),
        "ready": piper_ready(),
    }


@app.get("/api/voice/status")
def voice_status() -> dict[str, Any]:
    settings = load_settings()
    selected_voice = settings.get("app", {}).get("voice", {}).get("model")
    selected_whisper = settings.get("whisper", {}).get("model")
    return {
        "piper": piper_ready(),
        "whisper": whisper_status(selected_whisper),
        "selectedVoice": selected_voice,
        "selectedWhisper": selected_whisper,
    }


@app.get("/api/models")
def models() -> dict[str, Any]:
    settings = load_settings()
    runtime_status = runtime.status()
    providers = [
        {
            "name": spec.name,
            "label": spec.label,
            "backend": spec.backend,
            "gateway": spec.is_gateway,
            "local": spec.is_local,
            "oauth": spec.is_oauth,
            "defaultApiBase": spec.default_api_base,
            "detectByBaseKeyword": spec.detect_by_base_keyword,
            "detectByKeyPrefix": spec.detect_by_key_prefix,
        }
        for spec in PROVIDERS
    ]
    return {
        "current": {
            "provider": settings.get("provider", {}).get("name", "openrouter"),
            "model": settings.get("provider", {}).get("model", ""),
            "apiBase": settings.get("provider", {}).get("apiBase", ""),
            "apiKeyConfigured": bool(settings.get("provider", {}).get("apiKey")),
            "runtimeModel": runtime_status.model,
            "runtimeReady": runtime_status.ready,
        },
        "providers": providers,
    }


@app.get("/api/channels")
def channels() -> dict[str, Any]:
    return {"channels": list_channels()}


@app.get("/api/skills")
def skills() -> dict[str, Any]:
    return {"skills": list_skills()}


@app.post("/api/skills")
def skills_create(payload: SkillCreatePayload) -> dict[str, Any]:
    try:
        skill = create_skill_scaffold(payload.name, payload.description)
    except (FileExistsError, ValueError) as error:
        return {"ok": False, "message": str(error)}
    return {"ok": True, "skill": skill, "skills": list_skills()}


@app.get("/api/memory")
def memory() -> dict[str, Any]:
    return {"items": list_memory_items()}


@app.post("/api/memory")
def memory_action(payload: MemoryPayload) -> dict[str, Any]:
    if payload.action == "add":
        if not payload.text:
            return {"ok": False, "message": "Informe um texto para salvar na memoria."}
        item, _records = add_memory_record(payload.text)
        return {"ok": True, "item": item, "items": read_memory_records()}
    if payload.action == "delete":
        if not payload.id:
            return {"ok": False, "message": "Informe o id da memoria para excluir."}
        return {"ok": True, "items": delete_memory_record(payload.id)}
    if payload.action == "clear":
        return {"ok": True, "items": clear_memory_records()}
    return export_memory_payload()


@app.get("/api/history")
def history() -> dict[str, Any]:
    return {"sessions": runtime.history_sessions(include_messages=True)}


@app.post("/api/history")
def history_action(payload: HistoryPayload) -> dict[str, Any]:
    if payload.action == "delete":
        if not payload.id:
            return {"ok": False, "message": "Informe o id da conversa para excluir."}
        removed = runtime.delete_history_session(payload.id)
        if not removed:
            return {"ok": False, "message": "Sessao de historico nao encontrada."}
        return {"ok": True, "sessions": runtime.history_sessions()}
    runtime.clear_history_sessions()
    return {"ok": True, "sessions": runtime.history_sessions()}


@app.post("/api/history/export")
def history_export(payload: HistoryExportPayload) -> dict[str, Any]:
    try:
        return runtime.export_history(payload.sessionId, payload.format)
    except ValueError as error:
        return {"ok": False, "message": str(error)}


@app.get("/api/reminders")
def reminders() -> dict[str, Any]:
    return {"items": runtime.reminder_jobs()}


@app.post("/api/reminders")
def reminders_action(payload: ReminderPayload) -> dict[str, Any]:
    if payload.action == "add":
        text = (payload.text or "").strip()
        result = runtime.add_reminder(
            text,
            name=payload.name,
            after_minutes=payload.afterMinutes,
            at=payload.at,
            every_seconds=payload.everySeconds,
            cron_expr=payload.cronExpr,
            tz=payload.tz,
            deliver=payload.deliver,
        )
        return result
    if payload.action == "remove":
        if not payload.id:
            return {"ok": False, "message": "Informe o id do lembrete para excluir."}
        return runtime.remove_reminder(payload.id)
    return runtime.clear_reminders()


@app.get("/api/subagents")
def subagents() -> dict[str, Any]:
    return {"items": runtime.subagent_items(), "busy": runtime.subagents_busy()}


@app.post("/api/subagents")
def subagents_action(payload: SubagentPayload) -> dict[str, Any]:
    if payload.action == "cancel":
        if not payload.sessionKey:
            return {"ok": False, "message": "Informe a sessao dos subagentes para cancelar."}
        return runtime.cancel_subagents(payload.sessionKey)
    task = (payload.task or "").strip()
    if not task:
        return {"ok": False, "message": "Informe a tarefa do subagente."}
    return runtime.spawn_subagent(task, title=payload.title)


@app.get("/api/tasks")
def tasks() -> dict[str, Any]:
    return {"items": list_tasks()}


@app.get("/api/workspace")
def workspace() -> dict[str, Any]:
    return {"items": list_workspace_items(), "path": str(workspace_dir())}


@app.get("/api/logs")
def logs() -> dict[str, Any]:
    return {"lines": tail_lines(logs_file(), 80)}


@app.get("/api/tools")
def tools() -> dict[str, Any]:
    return {"tools": [{"name": name} for name in runtime.tool_names]}


@app.post("/api/provider/test")
def provider_test(payload: ProviderTestPayload) -> dict[str, Any]:
    settings = load_settings()
    provider = payload.provider or settings.get("provider", {}).get("name", "")
    model = payload.model or settings.get("provider", {}).get("model", "")
    api_key = payload.apiKey or settings.get("provider", {}).get("apiKey", "")
    if not api_key:
        return {"ok": False, "provider": provider, "model": model, "message": "Nenhuma chave de API configurada."}
    if not runtime.ready:
        return {"ok": False, "provider": provider, "model": model, "message": "O runtime local ainda nao esta pronto."}
    probe = runtime.chat("ping", session_key="provider:test")
    ok = not probe.lower().startswith("falha") and "nao esta pronto" not in probe.lower()
    return {
        "ok": ok,
        "provider": provider,
        "model": model,
        "message": probe if ok else "Nao foi possivel validar o provedor agora.",
    }


@app.post("/api/chat")
def chat(payload: ChatPayload) -> dict[str, Any]:
    session_id = payload.sessionId or "local"
    reply = runtime.chat(payload.message, session_key=f"bmo:{session_id}")
    return {
        "reply": reply,
        "sessionId": session_id,
    }


@app.post("/api/speak")
def speak(payload: SpeakPayload) -> dict[str, Any]:
    settings = load_settings()
    voice = payload.voice or settings.get("app", {}).get("voice", {}).get("model", "")
    try:
        return speak_text(payload.text, voice)
    except Exception as error:
        return {
            "ok": False,
            "message": str(error),
            "voice": voice,
            "audioDataUrl": "",
        }


@app.post("/api/whisper/test")
def whisper_test(payload: WhisperTestPayload | None = None) -> dict[str, Any]:
    model = (payload.model if payload else None) or load_settings().get("whisper", {}).get("model", "base")
    try:
        return test_whisper_runtime(model_name=model)
    except Exception as error:
        return {
            "ok": False,
            "message": str(error),
            "language": "pt",
            "transcript": "",
            "whisper": whisper_status(model),
        }
