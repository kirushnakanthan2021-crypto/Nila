"""
Human-gated patch export / apply.

- Never auto-edits files under nila/ (core engine).
- Writes only into workspace/ directory.
- Apply requires explicit confirmation string from the human.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path("workspace")
PROPOSALS_DIR = WORKSPACE / "proposals"
APPLIED_DIR = WORKSPACE / "applied"

# Paths that must never be overwritten by this helper
PROTECTED_PREFIXES = (
    "nila/",
    "tests/",
    ".github/",
    "main.py",
    "api.py",
)


def _ensure_dirs() -> None:
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    APPLIED_DIR.mkdir(parents=True, exist_ok=True)


def is_protected(relative_path: str) -> bool:
    p = relative_path.replace("\\", "/").lstrip("./")
    for prefix in PROTECTED_PREFIXES:
        if p == prefix.rstrip("/") or p.startswith(prefix):
            return True
    return False


def export_proposal_file(
    title: str,
    description: str,
    proposed_code: str,
    target_hint: str = "workspace/scratch.py",
) -> dict:
    """Save a proposal as a text file under workspace/proposals for human review."""
    _ensure_dirs()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:60]
    path = PROPOSALS_DIR / f"{stamp}_{safe_title}.md"
    body = (
        f"# Proposal: {title}\n\n"
        f"{description}\n\n"
        f"Suggested path hint: `{target_hint}`\n\n"
        f"## Code\n\n```python\n{proposed_code}\n```\n\n"
        f"## Apply rules\n"
        f"- Core paths under `nila/`, `tests/`, `main.py`, `api.py` are protected.\n"
        f"- Use CLI 'Apply workspace patch' only after you review.\n"
        f"- Type CONFIRM to write into workspace/ only.\n"
    )
    path.write_text(body, encoding="utf-8")
    return {"path": str(path), "title": title}


def write_workspace_file(
    relative_path: str,
    content: str,
    *,
    confirm: str,
) -> dict:
    """
    Write a file under workspace/ only.
    confirm must be exactly 'CONFIRM'.
    """
    if confirm != "CONFIRM":
        return {
            "ok": False,
            "error": "Refused: type CONFIRM exactly to apply.",
        }

    rel = relative_path.replace("\\", "/").lstrip("./")
    if not rel.startswith("workspace/"):
        rel = f"workspace/{rel}"

    if is_protected(rel):
        return {"ok": False, "error": f"Protected path refused: {rel}"}

    # prevent path escape
    target = Path(rel).resolve()
    workspace_root = WORKSPACE.resolve()
    if workspace_root not in target.parents and target != workspace_root:
        # target should be inside workspace
        try:
            target.relative_to(workspace_root)
        except ValueError:
            return {"ok": False, "error": "Path escapes workspace/."}

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    _ensure_dirs()
    log = APPLIED_DIR / f"applied_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
    log.write_text(f"Wrote {target}\nBytes: {len(content.encode('utf-8'))}\n", encoding="utf-8")

    return {"ok": True, "path": str(target)}


def list_proposal_files(limit: int = 20) -> list[str]:
    _ensure_dirs()
    files = sorted(PROPOSALS_DIR.glob("*.md"), reverse=True)
    return [str(p) for p in files[:limit]]
