"""
Safe-ish execution of short Python snippets.

Rules:
- Only runs code the human explicitly submits after seeing it.
- Runs in a subprocess with timeout (not in-process exec of untrusted code as the main app).
- No shell=True, no automatic use by the agent.
- Still not a perfect security boundary — do not run hostile code.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


FORBIDDEN_MARKERS = (
    "subprocess",
    "os.system",
    "os.popen",
    "pty.",
    "ctypes",
    "socket",
    "urllib",
    "requests",
    "shutil.rmtree",
    "pathlib.Path.unlink",
    "open(",  # discourage file writes from sandbox; allow only pure compute demos
    "__import__",
    "importlib",
    "exec(",
    "eval(",
    "compile(",
)


def safety_scan(code: str) -> list[str]:
    """Return list of blocked reasons if code looks dangerous for the sandbox."""
    lower = code.lower()
    hits = []
    for marker in FORBIDDEN_MARKERS:
        if marker.lower() in lower:
            hits.append(f"blocked pattern: {marker}")
    if "import os" in lower or "from os" in lower:
        hits.append("blocked pattern: os module")
    if "import sys" in lower and "sys.stdout" not in lower:
        # allow sys for printing demos is rare; keep simple — block broad sys use
        pass
    return hits


def run_python_snippet(
    code: str,
    timeout_sec: float = 3.0,
    *,
    force: bool = False,
) -> dict:
    """
    Run a short Python snippet in a temporary file via subprocess.

    Returns dict with ok, stdout, stderr, returncode, blocked.
    """
    code = code.strip()
    if not code:
        return {
            "ok": False,
            "blocked": True,
            "stdout": "",
            "stderr": "Empty code.",
            "returncode": -1,
        }

    if len(code) > 8000:
        return {
            "ok": False,
            "blocked": True,
            "stdout": "",
            "stderr": "Code too long for sandbox (max 8000 chars).",
            "returncode": -1,
        }

    hits = safety_scan(code)
    if hits and not force:
        return {
            "ok": False,
            "blocked": True,
            "stdout": "",
            "stderr": "Safety scan blocked this code:\n- " + "\n- ".join(hits),
            "returncode": -1,
            "blocked_reasons": hits,
        }

    with tempfile.TemporaryDirectory(prefix="nila_sandbox_") as tmp:
        path = Path(tmp) / "snippet.py"
        path.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(path)],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=tmp,
            )
            return {
                "ok": proc.returncode == 0,
                "blocked": False,
                "stdout": (proc.stdout or "")[:8000],
                "stderr": (proc.stderr or "")[:4000],
                "returncode": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "blocked": False,
                "stdout": "",
                "stderr": f"Timed out after {timeout_sec}s.",
                "returncode": -2,
            }
        except Exception as exc:
            return {
                "ok": False,
                "blocked": False,
                "stdout": "",
                "stderr": str(exc),
                "returncode": -3,
            }
