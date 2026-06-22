from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.core.config.paths import app_config_file, project_root, workspace_dir
from backend.core.config.settings import load_settings


def _default_logger(event: str, **fields: Any) -> None:
    try:
        payload = json.dumps({"event": event, **fields}, ensure_ascii=False, default=str)
        sys.stderr.write(payload + "\n")
    except Exception:
        pass


_ASYNC_LOOP: asyncio.AbstractEventLoop | None = None
_ASYNC_THREAD: threading.Thread | None = None
_ASYNC_LOCK = threading.Lock()


def _ensure_loop() -> asyncio.AbstractEventLoop:
    global _ASYNC_LOOP, _ASYNC_THREAD
    if _ASYNC_LOOP is not None and not _ASYNC_LOOP.is_closed():
        return _ASYNC_LOOP
    with _ASYNC_LOCK:
        if _ASYNC_LOOP is not None and not _ASYNC_LOOP.is_closed():
            return _ASYNC_LOOP
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=loop.run_forever, name="BmoRuntimeLoop", daemon=True)
        thread.start()
        _ASYNC_LOOP = loop
        _ASYNC_THREAD = thread
        return loop


def _run_async(coro: Any) -> Any:
    loop = _ensure_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=300)


@dataclass(slots=True)
class RuntimeStatus:
    ready: bool
    error: str = ""
    tool_count: int = 0
    workspace: str = ""
    config: str = ""
    source: str = ""
    provider: str = ""
    model: str = ""


class AgentRuntime:
    def __init__(self) -> None:
        self.root = project_root()
        self.workspace = workspace_dir()
        self.config_path = app_config_file()
        self._agent_loop: Any = None
        self._ready = False
        self._error = ""
        self._loaded = False
        self._tool_names: list[str] = []
        self._provider_name = ""
        self._model = ""

    def reload(self) -> None:
        self._loaded = False
        self._ready = False
        self._error = ""
        self._tool_names = []
        self._agent_loop = None

    def ensure_ready(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            if str(self.root) not in sys.path:
                sys.path.insert(0, str(self.root))

            from nanobot.agent.loop import AgentLoop
            from nanobot.config.schema import Config

            settings = load_settings()
            provider_settings = settings.get("provider", {}) if isinstance(settings, dict) else {}
            provider_name = str(provider_settings.get("name") or "openrouter").strip() or "openrouter"
            model = str(provider_settings.get("model") or "openai/gpt-oss-120b:free").strip()
            api_key = str(provider_settings.get("apiKey") or provider_settings.get("api_key") or "").strip()
            api_base = str(provider_settings.get("apiBase") or provider_settings.get("api_base") or "").strip()

            for key in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
                value = os.environ.get(key)
                if value:
                    os.environ[key] = value

            config = Config()
            config.agents.defaults.workspace = str(self.workspace)
            config.agents.defaults.model = model
            config.agents.defaults.provider = provider_name
            if provider_name == "openrouter":
                config.providers.openrouter.api_key = api_key
                config.providers.openrouter.api_base = api_base or config.providers.openrouter.api_base
            else:
                provider_cfg = getattr(config.providers, provider_name, None)
                if provider_cfg is not None:
                    if hasattr(provider_cfg, "api_key"):
                        provider_cfg.api_key = api_key
                    if hasattr(provider_cfg, "api_base") and api_base:
                        provider_cfg.api_base = api_base
            self._provider_name = provider_name
            self._model = model

            self._agent_loop = AgentLoop.from_config(config)
            self._ready = True
            self._error = ""
            self._tool_names = list(getattr(self._agent_loop, "tool_names", []))
            _default_logger(
                "runtime_ready",
                workspace=str(self.workspace),
                toolCount=len(self._tool_names),
            )
        except Exception as exc:
            self._ready = False
            self._error = str(exc)
            self._tool_names = []
            _default_logger("runtime_failed", error=str(exc))

    @property
    def ready(self) -> bool:
        self.ensure_ready()
        return self._ready

    @property
    def error(self) -> str:
        self.ensure_ready()
        return self._error

    @property
    def tool_names(self) -> list[str]:
        self.ensure_ready()
        return list(self._tool_names)

    def status(self) -> RuntimeStatus:
        self.ensure_ready()
        return RuntimeStatus(
            ready=self._ready,
            error=self._error,
            tool_count=len(self._tool_names),
            workspace=str(self.workspace),
            config=str(self.config_path),
            source=str(self.root),
            provider=self._provider_name,
            model=self._model,
        )

    def chat(self, message: str, session_key: str) -> str:
        self.ensure_ready()
        if not self._ready or self._agent_loop is None:
            return "O motor local ainda nao esta pronto. Configure o provedor e tente novamente."

        async def _call() -> str:
            result = await self._agent_loop.process_direct(
                content=message,
                session_key=session_key,
                channel="bmo_desktop",
                chat_id="local",
            )
            return (getattr(result, "content", "") or "").strip()

        try:
            return _run_async(_call()) or "Nao consegui montar uma resposta agora."
        except Exception as exc:
            self._error = str(exc)
            return f"Falha ao conversar com o motor local: {exc}"

    def tool_info(self, name: str) -> dict[str, Any]:
        self.ensure_ready()
        if not self._ready or self._agent_loop is None:
            return {"ok": False, "error": self._error or "runtime not ready"}
        for definition in getattr(self._agent_loop, "tool_definitions", lambda: [])():
            fn = definition.get("function", {}) if isinstance(definition, dict) else {}
            if fn.get("name") == name:
                return {"ok": True, "tool": definition}
        return {"ok": False, "error": f"Tool not found: {name}"}
