from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    root = _project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    os.environ.setdefault("BMO_HOME", str(Path.home() / ".bmo-v2"))
    token = secrets.token_hex(32)
    print(f"BMO_TOKEN={token}", flush=True)

    import uvicorn

    uvicorn.run(
        "backend.core.api.main:app",
        host="127.0.0.1",
        port=8787,
        reload=False,
        log_level="info",
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
