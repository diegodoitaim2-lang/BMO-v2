from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.core.agent.runtime import AgentRuntime
from backend.core.bootstrap import (
    build_bootstrap,
    build_system_snapshot,
    list_channels,
    list_history_sessions,
    list_memory_items,
    list_reminders,
    list_skills,
    list_subagents,
    list_tasks,
    list_voice_models,
    list_workspace_items,
)
from backend.core.config.paths import ensure_layout, logs_file, runtime_dir, workspace_dir
from backend.core.config.settings import load_settings, merge_settings
from backend.core.store import tail_lines


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


@app.on_event("startup")
def _startup() -> None:
    ensure_layout()
    runtime.ensure_ready()


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
    }


@app.get("/api/channels")
def channels() -> dict[str, Any]:
    return {"channels": list_channels()}


@app.get("/api/skills")
def skills() -> dict[str, Any]:
    return {"skills": list_skills()}


@app.get("/api/memory")
def memory() -> dict[str, Any]:
    return {"items": list_memory_items()}


@app.get("/api/history")
def history() -> dict[str, Any]:
    return {"sessions": list_history_sessions()}


@app.get("/api/reminders")
def reminders() -> dict[str, Any]:
    return {"items": list_reminders()}


@app.get("/api/subagents")
def subagents() -> dict[str, Any]:
    return {"items": list_subagents(), "busy": False}


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
    voice_path = runtime_dir() / "piper" / (voice or "pt_BR-faber-medium.onnx")
    if not voice_path.exists():
        return {"ok": False, "message": "Modelo de voz nao encontrado.", "voice": voice}
    return {"ok": True, "voice": voice, "message": "Voz disponivel para gerar audio quando o Piper estiver configurado."}


@app.post("/api/whisper/test")
def whisper_test(payload: WhisperTestPayload | None = None) -> dict[str, Any]:
    model = (payload.model if payload else None) or load_settings().get("whisper", {}).get("model", "base")
    whisper_exe = runtime_dir() / "whisper.cpp" / "Win32" / "Release" / "whisper-cli.exe"
    exists = whisper_exe.exists()
    return {
        "ok": exists,
        "message": "Whisper pronto." if exists else "Whisper ainda nao foi encontrado no runtime.",
        "mode": "local",
        "whisper": {"model": model, "exe": str(whisper_exe), "ready": exists},
    }
