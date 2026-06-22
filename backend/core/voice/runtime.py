from __future__ import annotations

import base64
import os
import re
import subprocess
import time
import wave
from pathlib import Path
from threading import Lock
from typing import Any

from backend.core.config.paths import app_home, runtime_dir, voices_dir
from backend.core.config.settings import load_settings

WHISPER_MODEL_FILES = {
    "tiny": "ggml-tiny.bin",
    "base": "ggml-base.bin",
    "small": "ggml-small.bin",
}

_STATE_LOCK = Lock()
_LAST_WHISPER_BACKEND = "cpu"
_LAST_WHISPER_ERROR = ""


def windows_process_options() -> tuple[Any, int]:
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return startupinfo, creationflags


def _voice_output_dir() -> Path:
    return app_home() / "voice"


def _piper_exe() -> Path:
    return runtime_dir() / "piper" / "piper" / "piper.exe"


def _piper_espeak_data() -> Path:
    return runtime_dir() / "piper" / "piper" / "espeak-ng-data"


def _whisper_exe() -> Path:
    return runtime_dir() / "whisper.cpp" / "Win32" / "Release" / "whisper-cli.exe"


def _whisper_models_dir() -> Path:
    return runtime_dir() / "whisper.cpp" / "models"


def _whisper_release_dir() -> Path:
    return runtime_dir() / "whisper.cpp" / "Win32" / "Release"


def _normalize_whisper_model(value: Any) -> str:
    selected = str(value or "base").strip().lower()
    return selected if selected in WHISPER_MODEL_FILES else "base"


def _normalize_language(value: str | None) -> str:
    language = str(value or "pt").strip().replace("_", "-")
    if not language:
        return "pt"
    return language.split("-", 1)[0].lower()


def _clean_speech_text(text: str) -> str:
    speech = str(text or "").strip()
    speech = re.sub(r"https?://\S+", "", speech)
    speech = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", speech)
    speech = re.sub(r"[*_`>#~|]+", "", speech)
    speech = re.sub(r"^\s*[-\u2022]\s+", "", speech, flags=re.M)
    speech = re.sub(r"\s*\n+\s*", ". ", speech)
    speech = re.sub(r"\s{2,}", " ", speech)
    return speech.strip()


def _voice_model_candidates() -> list[Path]:
    roots = [runtime_dir() / "piper", voices_dir()]
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.onnx")):
            try:
                if path.is_file() and path.stat().st_size > 1024 * 1024:
                    candidates.append(path)
            except OSError:
                continue
    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _resolve_piper_model_path(voice: str | None = None) -> Path:
    settings_voice = load_settings().get("app", {}).get("voice", {})
    requested = str(voice or settings_voice.get("model") or "pt_BR-faber-medium.onnx").strip()
    requested_path = Path(requested)
    if requested_path.is_absolute() and requested_path.exists():
        return requested_path
    if requested_path.exists():
        return requested_path.resolve()

    candidate_names = [requested_path.name] if requested_path.name else []
    search_roots = [runtime_dir() / "piper", voices_dir()]
    for root in search_roots:
        for name in candidate_names:
            candidate = root / name
            if candidate.exists():
                return candidate

    fallback = _voice_model_candidates()
    if fallback:
        return fallback[0]

    return runtime_dir() / "piper" / requested_path.name


def piper_ready() -> bool:
    return _piper_exe().exists() and _piper_espeak_data().exists() and bool(_voice_model_candidates())


def whisper_gpu_backends() -> list[dict[str, str]]:
    release_dir = _whisper_release_dir()
    backends: list[dict[str, str]] = []
    if (release_dir / "ggml-vulkan.dll").exists():
        backends.append({"id": "vulkan", "label": "Vulkan"})
    if (release_dir / "ggml-cuda.dll").exists():
        backends.append({"id": "cuda", "label": "CUDA"})
    return backends


def whisper_config() -> dict[str, Any]:
    raw = load_settings().get("whisper", {})
    if not isinstance(raw, dict):
        raw = {}
    return {
        "gpu_enabled": bool(raw.get("gpu_enabled", True)),
        "gpu_index": int(raw.get("gpu_index", 0) or 0),
        "model": _normalize_whisper_model(raw.get("model")),
        "fallback_to_cpu": bool(raw.get("fallback_to_cpu", True)),
    }


def resolve_whisper_model_path(model_name: str | None = None) -> Path:
    selected = _normalize_whisper_model(model_name or whisper_config().get("model"))
    return _whisper_models_dir() / WHISPER_MODEL_FILES[selected]


def whisper_ready(model_name: str | None = None) -> bool:
    return _whisper_exe().exists() and resolve_whisper_model_path(model_name).exists()


def whisper_status(model_name: str | None = None) -> dict[str, Any]:
    config = whisper_config()
    if model_name is not None:
        config["model"] = _normalize_whisper_model(model_name)
    model_path = resolve_whisper_model_path(str(config.get("model")))
    backends = whisper_gpu_backends()
    with _STATE_LOCK:
        last_mode = _LAST_WHISPER_BACKEND
        last_error = _LAST_WHISPER_ERROR
    return {
        **config,
        "exe": str(_whisper_exe()),
        "modelPath": str(model_path),
        "models": [
            {
                "id": key,
                "label": key,
                "file": file_name,
                "path": str(_whisper_models_dir() / file_name),
                "exists": (_whisper_models_dir() / file_name).exists(),
            }
            for key, file_name in WHISPER_MODEL_FILES.items()
        ],
        "gpuCapable": bool(backends),
        "gpuBackends": backends,
        "runtimeMessage": "GPU disponivel" if backends else "Runtime atual do Whisper e CPU-only",
        "lastMode": last_mode,
        "lastError": last_error,
        "ready": whisper_ready(model_name or str(config.get("model"))),
        "message": "Whisper pronto." if whisper_ready(model_name or str(config.get("model"))) else "Whisper ainda nao foi encontrado no runtime.",
    }


def windows_model_label(path: Path) -> str:
    return path.stem.replace("_", " ")


def _run_piper_command(command: list[str], speech: str) -> subprocess.CompletedProcess[str]:
    startupinfo, creationflags = windows_process_options()
    return subprocess.run(
        command,
        input=speech,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        startupinfo=startupinfo,
        creationflags=creationflags,
        timeout=180,
    )


def speak_text(text: str, voice: str = "") -> dict[str, Any]:
    speech = _clean_speech_text(text)
    if not speech:
        return {"ok": False, "message": "Texto vazio para falar.", "voice": voice}

    selected = _resolve_piper_model_path(voice)
    if not _piper_exe().exists():
        return {"ok": False, "message": "Piper nao encontrado no runtime.", "voice": selected.name}
    if not selected.exists():
        return {"ok": False, "message": "Modelo de voz nao encontrado.", "voice": selected.name}
    if not _piper_espeak_data().exists():
        return {"ok": False, "message": "Dados do espeak-ng nao encontrados no runtime.", "voice": selected.name}

    output_dir = _voice_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / "bmo_reply.wav"
    if wav_path.exists():
        try:
            wav_path.unlink()
        except OSError:
            pass

    command = [
        str(_piper_exe()),
        "--model",
        str(selected),
        "--output_file",
        str(wav_path),
        "--espeak_data",
        str(_piper_espeak_data()),
        "--quiet",
    ]

    t0 = time.perf_counter()
    try:
        _run_piper_command(command, speech)
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()
        message = detail or "Falha ao gerar audio com o Piper."
        return {"ok": False, "message": message, "voice": selected.name}

    piper_ms = round((time.perf_counter() - t0) * 1000)
    if not wav_path.exists():
        return {"ok": False, "message": "Piper terminou sem gerar o WAV.", "voice": selected.name}

    audio_bytes = wav_path.read_bytes()
    audio_data_url = "data:audio/wav;base64," + base64.b64encode(audio_bytes).decode("ascii")
    try:
        with wave.open(str(wav_path), "rb") as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate() or 1
            duration_ms = round(frames / rate * 1000)
    except wave.Error:
        duration_ms = 0

    return {
        "ok": True,
        "message": "Audio gerado com sucesso.",
        "voice": selected.name,
        "voicePath": str(selected),
        "audioPath": str(wav_path),
        "audioDataUrl": audio_data_url,
        "durationMs": duration_ms,
        "piperMs": piper_ms,
        "spokenText": speech,
    }


def _run_whisper_command(command: list[str], mode: str) -> str:
    global _LAST_WHISPER_BACKEND, _LAST_WHISPER_ERROR
    startupinfo, creationflags = windows_process_options()
    result = subprocess.run(
        command,
        cwd=str(_whisper_exe().parent),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=startupinfo,
        creationflags=creationflags,
        timeout=180,
    )
    with _STATE_LOCK:
        _LAST_WHISPER_BACKEND = mode
    if result.returncode != 0:
        error_text = (result.stderr or result.stdout or "").strip()
        with _STATE_LOCK:
            _LAST_WHISPER_ERROR = error_text
        raise RuntimeError(f"Whisper falhou ({result.returncode}): {error_text or 'erro desconhecido'}")

    transcript = (result.stdout or "").strip()
    if not transcript:
        error_text = (result.stderr or "").strip()
        with _STATE_LOCK:
            _LAST_WHISPER_ERROR = error_text or "Nenhuma fala detectada."
        raise RuntimeError(_LAST_WHISPER_ERROR)

    with _STATE_LOCK:
        _LAST_WHISPER_ERROR = ""
    return transcript


def record_microphone(seconds: float = 5.0, samplerate: int = 16000) -> Path:
    try:
        import numpy as np
        import sounddevice as sd
    except Exception as error:
        raise RuntimeError("Dependencias de captura de audio nao estao disponiveis.") from error

    output_dir = _voice_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / "whisper_test.wav"

    try:
        sd.query_devices(kind="input")
    except Exception as error:
        raise RuntimeError("Nenhum microfone de entrada configurado.") from error

    frames = max(1, int(seconds * samplerate))
    try:
        recording = sd.rec(frames, samplerate=samplerate, channels=1, dtype="int16")
        sd.wait()
    except Exception as error:
        raise RuntimeError(f"Nao foi possivel gravar o microfone: {error}") from error

    if recording is None or not getattr(recording, "size", 0):
        raise RuntimeError("Nenhum som capturado do microfone.")

    peak = int(np.max(np.abs(recording)))
    if peak < 40:
        raise RuntimeError("Nenhuma fala detectada no microfone.")

    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(samplerate)
        wav_file.writeframes(recording.astype("int16", copy=False).tobytes())

    return wav_path


def transcribe_wav(wav_path: Path, language: str = "pt", model_name: str | None = None) -> str:
    whisper_exe = _whisper_exe()
    if not whisper_exe.exists():
        raise RuntimeError("whisper-cli.exe nao encontrado no runtime.")

    model_path = resolve_whisper_model_path(model_name)
    if not model_path.exists():
        raise RuntimeError("Modelo Whisper nao encontrado.")

    normalized_language = _normalize_language(language)
    base_command = [
        str(whisper_exe),
        "--model",
        str(model_path),
        "--file",
        str(wav_path),
        "--language",
        normalized_language,
        "--no-timestamps",
        "--no-prints",
    ]
    config = whisper_config()
    if config["gpu_enabled"] and whisper_gpu_backends():
        try:
            return _run_whisper_command(base_command, "gpu")
        except Exception:
            if not config["fallback_to_cpu"]:
                raise
    return _run_whisper_command([*base_command, "--no-gpu"], "cpu")


def test_whisper_runtime(model_name: str | None = None, seconds: float = 4.0, language: str | None = None) -> dict[str, Any]:
    selected_model = _normalize_whisper_model(model_name or whisper_config().get("model"))
    selected_language = _normalize_language(language or load_settings().get("app", {}).get("language", "pt-BR"))
    try:
        wav_path = record_microphone(seconds=seconds)
        try:
            transcript = transcribe_wav(wav_path, selected_language, selected_model)
            used_language = selected_language
        except Exception as first_error:
            if selected_language == "en":
                raise first_error
            transcript = transcribe_wav(wav_path, "en", selected_model)
            used_language = "en"
        status = whisper_status(selected_model)
        return {
            "ok": True,
            "message": "Microfone gravado e transcrito com sucesso.",
            "language": used_language,
            "transcript": transcript,
            "audioPath": str(wav_path),
            "whisper": status,
        }
    except Exception as error:
        status = whisper_status(selected_model)
        return {
            "ok": False,
            "message": str(error),
            "language": selected_language,
            "transcript": "",
            "whisper": status,
        }


__all__ = [
    "piper_ready",
    "record_microphone",
    "resolve_whisper_model_path",
    "speak_text",
    "test_whisper_runtime",
    "transcribe_wav",
    "windows_process_options",
    "whisper_config",
    "whisper_gpu_backends",
    "whisper_ready",
    "whisper_status",
]
