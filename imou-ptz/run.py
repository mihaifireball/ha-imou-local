"""Home Assistant add-on launcher for the IMOU PTZ proxy."""

import json
import os
import sys
from pathlib import Path


OPTIONS_FILE = Path("/data/options.json")


def fail(message: str) -> None:
    print(f"[imou-ptz] ERROR: {message}", file=sys.stderr, flush=True)
    raise SystemExit(1)


try:
    options = json.loads(OPTIONS_FILE.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    fail(f"Cannot read add-on options: {exc}")

host = str(options.get("camera_host", "")).strip()
username = str(options.get("username", "admin")).strip()
password = str(options.get("password", ""))

try:
    port = int(options.get("dvrip_port", 37777))
except (TypeError, ValueError):
    fail("dvrip_port must be an integer")

if not host:
    fail("camera_host is required")
if not username:
    fail("username is required")
if not password:
    fail("password is required")
if not 1 <= port <= 65535:
    fail("dvrip_port must be between 1 and 65535")

env = os.environ.copy()
env.update(
    {
        "CAMERA_HOST": host,
        "CAMERA_DVRIP_PORT": str(port),
        "CAMERA_USER": username,
        "CAMERA_PASSWORD": password,
        "API_PORT": "8000",
        "PYTHONUNBUFFERED": "1",
    }
)

print(f"[imou-ptz] Starting local proxy for {host}:{port}", flush=True)
os.execvpe(
    "python3",
    ["python3", "-m", "imou_ptz", "serve", "--bind", "0.0.0.0", "--api-port", "8000"],
    env,
)

