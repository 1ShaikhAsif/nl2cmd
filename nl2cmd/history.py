"""Translation history logging and search."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

HISTORY_FILE = Path.home() / ".nl2cmd_history"


@dataclass
class HistoryEntry:
    """A single translation history entry."""

    query: str
    command: str
    mode: str  # "rule", "ai", "hybrid"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    executed: bool = False
    rule_intent: str | None = None


def _load_history(path: Path = HISTORY_FILE) -> list[dict]:
    """Load history entries from the JSON file."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(entries: list[dict], path: Path = HISTORY_FILE) -> None:
    """Save history entries to the JSON file."""
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")


def log_translation(entry: HistoryEntry, path: Path = HISTORY_FILE) -> None:
    """Append a translation to the history file."""
    entries = _load_history(path)
    entries.append(asdict(entry))
    _save_history(entries, path)


def search_history(
    query: str = "",
    limit: int = 20,
    path: Path = HISTORY_FILE,
) -> list[dict]:
    """Search translation history by query substring.

    Returns the most recent matching entries, up to `limit`.
    """
    entries = _load_history(path)

    if query:
        query_lower = query.lower()
        entries = [
            e for e in entries
            if query_lower in e.get("query", "").lower()
            or query_lower in e.get("command", "").lower()
        ]

    return entries[-limit:]


def clear_history(path: Path = HISTORY_FILE) -> None:
    """Clear all history entries."""
    _save_history([], path)
