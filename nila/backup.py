"""Export / import knowledge as JSON (portable backup, not the full SQLite file)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .store import Store
from . import __version__


def export_knowledge_json(store: Store, path: str | Path, limit: int = 5000) -> dict[str, Any]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    items = store.recent_knowledge(limit=limit)
    # recent_knowledge is DESC; keep as-is for readability
    payload = {
        "format": "nila-knowledge-v1",
        "nila_version": __version__,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "knowledge": [
            {
                "title": it.get("title", ""),
                "content": it.get("content", ""),
                "source": it.get("source", ""),
                "verified": bool(it.get("verified")),
                "topic": it.get("topic", ""),
            }
            for it in items
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    store.log_interaction("export_knowledge", str(path))
    return {"path": str(path), "count": len(items)}


def import_knowledge_json(
    store: Store, path: str | Path, *,
    skip_duplicates: bool = True,
) -> dict[str, Any]:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "knowledge" not in data:
        raise ValueError("Invalid Nila knowledge backup (missing knowledge array).")
    existing = {
        (x.get("title", "").strip().lower(), x.get("content", "").strip()[:120])
        for x in store.recent_knowledge(limit=5000)
    }
    added = 0
    skipped = 0
    for row in data.get("knowledge") or []:
        title = str(row.get("title", "")).strip()
        content = str(row.get("content", "")).strip()
        if not title or not content:
            skipped += 1
            continue
        key = (title.lower(), content[:120])
        if skip_duplicates and key in existing:
            skipped += 1
            continue
        store.add_knowledge(
            title=title,
            content=content,
            source=str(row.get("source") or "imported backup"),
            verified=bool(row.get("verified")),
            topic=str(row.get("topic") or ""),
        )
        existing.add(key)
        added += 1
    store.log_interaction("import_knowledge", f"added={added} skipped={skipped}")
    return {"added": added, "skipped": skipped, "path": str(path)}
