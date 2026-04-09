#!/usr/bin/env python3
"""Start Django and Vite together for local development.

Defaults:
- Django:  http://0.0.0.0:8080
- Vite:    http://localhost:5173

Usage:
    python scripts/dev.py
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
DJANGO_PORT = os.environ.get("DJANGO_PORT", "8080")
VITE_PORT = os.environ.get("VITE_PORT", "5173")
DJANGO_HOST = os.environ.get("DJANGO_HOST", "0.0.0.0")
VITE_HOST = os.environ.get("VITE_HOST", "0.0.0.0")


def pick_python() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    print(f"Warning: {VENV_PYTHON} not found, falling back to {sys.executable}")
    return sys.executable


def build_commands() -> tuple[list[str], list[str]]:
    python_cmd = pick_python()
    django_cmd = [python_cmd, "manage.py", "runserver", f"{DJANGO_HOST}:{DJANGO_PORT}"]
    vite_cmd = ["npm", "run", "dev", "--", "--host", VITE_HOST, "--port", VITE_PORT]
    return django_cmd, vite_cmd


def start_process(command: list[str], cwd: Path, name: str) -> subprocess.Popen:
    print(f"Starting {name}: {' '.join(command)}")
    return subprocess.Popen(command, cwd=cwd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Start Django and Vite together.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without starting servers.")
    args = parser.parse_args()

    django_cmd, vite_cmd = build_commands()

    print("Local dev servers:")
    print(f"  Django: http://{DJANGO_HOST}:{DJANGO_PORT}")
    print(f"  Vite:   http://localhost:{VITE_PORT}")
    print()

    if args.dry_run:
        print("Dry run mode; not starting processes.")
        print(f"Django command: {' '.join(django_cmd)}")
        print(f"Vite command:   {' '.join(vite_cmd)}")
        return 0

    django_proc = start_process(django_cmd, ROOT, "Django")
    vite_proc = start_process(vite_cmd, FRONTEND_DIR, "Vite")

    processes = [django_proc, vite_proc]

    def shutdown(*_args: object) -> None:
        print("\nStopping dev servers...")
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
        for proc in processes:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            for proc in processes:
                code = proc.poll()
                if code is not None:
                    shutdown()
                    return code
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

