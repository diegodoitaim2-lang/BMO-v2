from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
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
        self._cron_service: Any = None
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
            from nanobot.cron.service import CronService
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

            if self._cron_service is None:
                cron_store = self.workspace / "cron" / "jobs.json"
                self._cron_service = CronService(cron_store, on_job=self._handle_cron_job)
            else:
                self._cron_service.on_job = self._handle_cron_job

            self._agent_loop = AgentLoop.from_config(
                config,
                cron_service=self._cron_service,
            )
            if self._cron_service is not None:
                _run_async(self._cron_service.start())
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

    async def _handle_cron_job(self, job: Any) -> str | None:
        agent = self._agent_loop
        if agent is None:
            return None

        payload = getattr(job, "payload", None)
        message = str(getattr(payload, "message", "") or "").strip()
        if not message and getattr(payload, "kind", "agent_turn") != "agent_turn":
            return None

        cron_tool = None
        cron_token = None
        with contextlib.suppress(Exception):
            cron_tool = agent.tools.get("cron") if getattr(agent, "tools", None) else None
        if cron_tool is not None:
            with contextlib.suppress(Exception):
                from nanobot.agent.tools.cron import CronTool

                if isinstance(cron_tool, CronTool):
                    cron_token = cron_tool.set_cron_context(True)

        try:
            response = await agent.process_direct(
                message or job.name,
                session_key=str(getattr(payload, "session_key", None) or f"cron:{job.id}"),
                channel=str(getattr(payload, "channel", None) or "bmo_desktop"),
                chat_id=str(getattr(payload, "to", None) or "reminders"),
                ephemeral=True,
            )
            return (getattr(response, "content", "") or "").strip() or None
        finally:
            if cron_tool is not None and cron_token is not None:
                with contextlib.suppress(Exception):
                    from nanobot.agent.tools.cron import CronTool

                    if isinstance(cron_tool, CronTool):
                        cron_tool.reset_cron_context(cron_token)

    def shutdown(self) -> None:
        if self._cron_service is not None:
            with contextlib.suppress(Exception):
                self._cron_service.stop()

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

    def subagents_busy(self) -> bool:
        self.ensure_ready()
        agent = self._agent_loop
        if agent is None:
            return False
        manager = getattr(agent, "subagents", None)
        if manager is None:
            return False
        try:
            return bool(manager.get_running_count())
        except Exception:
            return False

    @staticmethod
    def _seconds_from_iso(value: str | None) -> int | None:
        if not value:
            return None
        try:
            return int(datetime.fromisoformat(value).timestamp())
        except ValueError:
            return None

    @staticmethod
    def _seconds_from_ms(value: int | None) -> int | None:
        if value is None:
            return None
        return int(value / 1000)

    @staticmethod
    def _format_seconds(value: int | None) -> str | None:
        if value is None:
            return None
        return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _describe_schedule(schedule: Any) -> str:
        kind = getattr(schedule, "kind", "")
        if kind == "at":
            at_ms = getattr(schedule, "at_ms", None)
            if at_ms is not None:
                when = datetime.fromtimestamp(at_ms / 1000).strftime("%Y-%m-%d %H:%M")
                return f"em {when}"
            return "agendado"
        if kind == "every":
            every_ms = getattr(schedule, "every_ms", None)
            if every_ms:
                if every_ms % 3_600_000 == 0:
                    return f"a cada {every_ms // 3_600_000}h"
                if every_ms % 60_000 == 0:
                    return f"a cada {every_ms // 60_000}min"
                return f"a cada {every_ms // 1000}s"
            return "recorrente"
        if kind == "cron":
            expr = getattr(schedule, "expr", "") or ""
            tz = getattr(schedule, "tz", "") or ""
            return f"cron {expr}{f' ({tz})' if tz else ''}".strip()
        return str(kind or "agendado")

    def history_sessions(self, *, include_messages: bool = False, message_limit: int = 50) -> list[dict[str, Any]]:
        self.ensure_ready()
        agent = self._agent_loop
        if agent is None:
            return []

        sessions = list(agent.sessions.list_sessions())
        items: list[dict[str, Any]] = []
        for session in sessions:
            key = str(session.get("key") or "").strip()
            if not key:
                continue
            item: dict[str, Any] = {
                "id": key,
                "title": str(session.get("title") or key),
                "preview": str(session.get("preview") or ""),
                "createdAt": self._seconds_from_iso(str(session.get("created_at") or "")),
                "updatedAt": self._seconds_from_iso(str(session.get("updated_at") or "")),
            }
            if include_messages:
                raw_session = agent.sessions.read_session_file(key)
                raw_messages = raw_session.get("messages", []) if isinstance(raw_session, dict) else []
                mapped_messages: list[dict[str, Any]] = []
                if isinstance(raw_messages, list):
                    for raw in raw_messages[-message_limit:]:
                        if not isinstance(raw, dict):
                            continue
                        content = str(raw.get("content") or raw.get("text") or "").strip()
                        if not content:
                            continue
                        mapped_messages.append({
                            "role": str(raw.get("role") or "user"),
                            "text": content,
                            "createdAt": self._seconds_from_iso(str(raw.get("timestamp") or "")),
                        })
                item["messages"] = mapped_messages
            items.append(item)
        return items

    def delete_history_session(self, session_id: str) -> bool:
        self.ensure_ready()
        agent = self._agent_loop
        if agent is None:
            return False
        try:
            return bool(agent.sessions.delete_session(session_id))
        except Exception:
            return False

    def clear_history_sessions(self) -> list[dict[str, Any]]:
        self.ensure_ready()
        agent = self._agent_loop
        if agent is None:
            return []
        for session in list(agent.sessions.list_sessions()):
            key = str(session.get("key") or "").strip()
            if key:
                with contextlib.suppress(Exception):
                    agent.sessions.delete_session(key)
        return []

    def export_history(self, session_id: str | None, fmt: str = "json") -> dict[str, Any]:
        sessions = self.history_sessions(include_messages=True)
        selected = sessions
        if session_id:
            selected = [item for item in sessions if str(item.get("id")) == str(session_id)]
            if not selected:
                raise ValueError("Sessao de historico nao encontrada.")

        fmt_normalized = (fmt or "json").lower()
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        base = "BMO_historico" if not session_id else f"BMO_historico_{session_id.replace(':', '_')}"

        if fmt_normalized == "md":
            lines: list[str] = []
            for session in selected:
                lines.append(f"# {session.get('title') or session.get('id')}")
                if session.get("id"):
                    lines.append(f"- ID: {session.get('id')}")
                created = self._format_seconds(session.get("createdAt"))
                updated = self._format_seconds(session.get("updatedAt"))
                if created:
                    lines.append(f"- Criado em: {created}")
                if updated:
                    lines.append(f"- Atualizado em: {updated}")
                lines.append("")
                for message in session.get("messages", []) if isinstance(session.get("messages"), list) else []:
                    if not isinstance(message, dict):
                        continue
                    role = str(message.get("role") or "user").strip().title()
                    text = str(message.get("text") or "").strip()
                    if text:
                        lines.append(f"## {role}")
                        lines.append(text)
                        lines.append("")
            content = "\n".join(lines).strip() or "# Historico\n\nSem conversas."
            return {
                "ok": True,
                "filename": f"{base}_{stamp}.md",
                "content": content,
                "mime": "text/markdown",
                "format": "md",
                "count": len(selected),
            }

        if fmt_normalized == "txt":
            lines = []
            for session in selected:
                lines.append(session.get("title") or session.get("id") or "Conversa")
                if session.get("id"):
                    lines.append(f"ID: {session.get('id')}")
                created = self._format_seconds(session.get("createdAt"))
                updated = self._format_seconds(session.get("updatedAt"))
                if created:
                    lines.append(f"Criado em: {created}")
                if updated:
                    lines.append(f"Atualizado em: {updated}")
                lines.append("")
                for message in session.get("messages", []) if isinstance(session.get("messages"), list) else []:
                    if not isinstance(message, dict):
                        continue
                    text = str(message.get("text") or "").strip()
                    if text:
                        lines.append(f"{message.get('role', 'user')}: {text}")
                lines.append("")
            content = "\n".join(lines).strip() or "Historico vazio."
            return {
                "ok": True,
                "filename": f"{base}_{stamp}.txt",
                "content": content,
                "mime": "text/plain",
                "format": "txt",
                "count": len(selected),
            }

        content = json.dumps(
            {"exportedAt": datetime.now().isoformat(), "sessions": selected},
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

    def reminder_jobs(self, include_disabled: bool = True) -> list[dict[str, Any]]:
        self.ensure_ready()
        service = self._cron_service
        if service is None:
            return []
        items: list[dict[str, Any]] = []
        for job in service.list_jobs(include_disabled=include_disabled):
            payload = getattr(job, "payload", None)
            schedule = getattr(job, "schedule", None)
            state = getattr(job, "state", None)
            if payload is None or schedule is None or state is None:
                continue
            if getattr(payload, "kind", "agent_turn") not in {"agent_turn", "system_event"}:
                continue
            items.append({
                "id": job.id,
                "name": job.name,
                "text": getattr(payload, "message", "") or job.name,
                "status": "desativado" if not job.enabled else (getattr(state, "last_status", None) or "ativo"),
                "dueAt": self._seconds_from_ms(getattr(state, "next_run_at_ms", None) or getattr(schedule, "at_ms", None)),
                "nextRunAt": self._seconds_from_ms(getattr(state, "next_run_at_ms", None)),
                "lastRunAt": self._seconds_from_ms(getattr(state, "last_run_at_ms", None)),
                "lastError": getattr(state, "last_error", None),
                "enabled": bool(job.enabled),
                "deliver": bool(getattr(payload, "deliver", False)),
                "channel": getattr(payload, "channel", None),
                "sessionKey": getattr(payload, "session_key", None),
                "schedule": self._describe_schedule(schedule),
            })
        return items

    def add_reminder(
        self,
        text: str,
        *,
        name: str | None = None,
        after_minutes: int | None = None,
        at: str | None = None,
        every_seconds: int | None = None,
        cron_expr: str | None = None,
        tz: str | None = None,
        deliver: bool = True,
    ) -> dict[str, Any]:
        self.ensure_ready()
        service = self._cron_service
        if service is None:
            return {"ok": False, "message": "Cron ainda nao esta pronto."}
        message = text.strip()
        if not message:
            return {"ok": False, "message": "Informe um texto para o lembrete."}

        from nanobot.cron.types import CronSchedule

        schedule: CronSchedule | None = None
        if after_minutes is not None and after_minutes > 0:
            schedule = CronSchedule(kind="at", at_ms=int((datetime.now().timestamp() + (after_minutes * 60)) * 1000))
        elif at:
            try:
                parsed = datetime.fromisoformat(at)
            except ValueError:
                return {"ok": False, "message": "Formato de data/hora invalido."}
            schedule = CronSchedule(kind="at", at_ms=int(parsed.timestamp() * 1000))
        elif every_seconds is not None and every_seconds > 0:
            schedule = CronSchedule(kind="every", every_ms=every_seconds * 1000)
        elif cron_expr:
            schedule = CronSchedule(kind="cron", expr=cron_expr, tz=tz or "America/Sao_Paulo")
        else:
            return {"ok": False, "message": "Informe o prazo do lembrete."}

        async def _call() -> dict[str, Any]:
            job = service.add_job(
                name=name or message[:30],
                schedule=schedule,
                message=message,
                deliver=deliver,
                channel="bmo_desktop",
                to="local",
                session_key="bmo:reminders",
            )
            return {"ok": True, "item": self.reminder_jobs_item(job), "items": self.reminder_jobs()}

        return _run_async(_call())

    def reminder_jobs_item(self, job: Any) -> dict[str, Any]:
        payload = getattr(job, "payload", None)
        schedule = getattr(job, "schedule", None)
        state = getattr(job, "state", None)
        return {
            "id": job.id,
            "name": job.name,
            "text": getattr(payload, "message", "") or job.name,
            "status": "desativado" if not job.enabled else (getattr(state, "last_status", None) or "ativo"),
            "dueAt": self._seconds_from_ms(getattr(state, "next_run_at_ms", None) or getattr(schedule, "at_ms", None)),
            "nextRunAt": self._seconds_from_ms(getattr(state, "next_run_at_ms", None)),
            "lastRunAt": self._seconds_from_ms(getattr(state, "last_run_at_ms", None)),
            "lastError": getattr(state, "last_error", None),
            "enabled": bool(job.enabled),
            "deliver": bool(getattr(payload, "deliver", False)),
            "channel": getattr(payload, "channel", None),
            "sessionKey": getattr(payload, "session_key", None),
            "schedule": self._describe_schedule(schedule),
        }

    def remove_reminder(self, reminder_id: str) -> dict[str, Any]:
        self.ensure_ready()
        service = self._cron_service
        if service is None:
            return {"ok": False, "message": "Cron ainda nao esta pronto."}
        async def _call() -> str:
            return service.remove_job(reminder_id)

        result = _run_async(_call())
        if result != "removed":
            return {"ok": False, "message": "Nao consegui remover o lembrete."}
        return {"ok": True, "items": self.reminder_jobs()}

    def clear_reminders(self) -> dict[str, Any]:
        self.ensure_ready()
        service = self._cron_service
        if service is None:
            return {"ok": False, "message": "Cron ainda nao esta pronto."}
        async def _call() -> list[dict[str, Any]]:
            for job in list(service.list_jobs(include_disabled=True)):
                with contextlib.suppress(Exception):
                    service.remove_job(job.id)
            return self.reminder_jobs()

        return {"ok": True, "items": _run_async(_call())}

    def spawn_subagent(self, task: str, title: str | None = None) -> dict[str, Any]:
        self.ensure_ready()
        agent = self._agent_loop
        if agent is None:
            return {"ok": False, "message": "Runtime ainda nao esta pronto."}
        subagents = getattr(agent, "subagents", None)
        if subagents is None:
            return {"ok": False, "message": "Subagentes nao estao disponiveis agora."}
        async def _call() -> str:
            return await subagents.spawn(
                task=task,
                label=title or None,
                origin_channel="bmo_desktop",
                origin_chat_id="local",
                session_key="bmo:desktop",
            )

        response = _run_async(_call())
        return {"ok": True, "message": response, "items": self.subagent_items(), "busy": self.subagents_busy()}

    def cancel_subagents(self, session_key: str) -> dict[str, Any]:
        self.ensure_ready()
        agent = self._agent_loop
        if agent is None:
            return {"ok": False, "message": "Runtime ainda nao esta pronto."}
        subagents = getattr(agent, "subagents", None)
        if subagents is None:
            return {"ok": False, "message": "Subagentes nao estao disponiveis agora."}
        key = session_key.strip()
        if not key:
            return {"ok": False, "message": "Informe a sessao dos subagentes para cancelar."}

        async def _call() -> int:
            return await subagents.cancel_by_session(key)

        cancelled = _run_async(_call())
        return {"ok": True, "cancelled": cancelled, "items": self.subagent_items(), "busy": self.subagents_busy()}

    def subagent_items(self) -> list[dict[str, Any]]:
        self.ensure_ready()
        agent = self._agent_loop
        if agent is None:
            return []
        manager = getattr(agent, "subagents", None)
        if manager is None:
            return []
        statuses = getattr(manager, "_task_statuses", {})
        items: list[dict[str, Any]] = []
        if isinstance(statuses, dict):
            for status in statuses.values():
                items.append({
                    "id": getattr(status, "task_id", ""),
                    "title": getattr(status, "label", "") or getattr(status, "task_description", "")[:30],
                    "status": getattr(status, "phase", "running"),
                    "iteration": getattr(status, "iteration", 0),
                    "result": getattr(status, "stop_reason", None),
                    "error": getattr(status, "error", None),
                    "startedAt": None,
                })
        return items

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
