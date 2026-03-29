"""Tests for the history module."""

from pathlib import Path

import pytest

from nl2cmd.history import HistoryEntry, clear_history, log_translation, search_history


@pytest.fixture
def tmp_history(tmp_path):
    """Create a temporary history file path."""
    return tmp_path / "test_history.json"


class TestHistory:
    def test_log_and_search(self, tmp_history):
        entry = HistoryEntry(
            query="find large files",
            command="find . -size +100M",
            mode="rule",
        )
        log_translation(entry, tmp_history)

        results = search_history("large", path=tmp_history)
        assert len(results) == 1
        assert results[0]["query"] == "find large files"

    def test_search_empty(self, tmp_history):
        results = search_history("anything", path=tmp_history)
        assert len(results) == 0

    def test_search_by_command(self, tmp_history):
        entry = HistoryEntry(
            query="open ports",
            command="ss -tulnp",
            mode="rule",
        )
        log_translation(entry, tmp_history)

        results = search_history("ss", path=tmp_history)
        assert len(results) == 1

    def test_multiple_entries(self, tmp_history):
        for i in range(5):
            log_translation(
                HistoryEntry(query=f"query {i}", command=f"cmd {i}", mode="rule"),
                tmp_history,
            )

        results = search_history(path=tmp_history)
        assert len(results) == 5

    def test_limit(self, tmp_history):
        for i in range(30):
            log_translation(
                HistoryEntry(query=f"query {i}", command=f"cmd {i}", mode="rule"),
                tmp_history,
            )

        results = search_history(limit=10, path=tmp_history)
        assert len(results) == 10

    def test_clear_history(self, tmp_history):
        log_translation(
            HistoryEntry(query="test", command="test", mode="rule"),
            tmp_history,
        )
        clear_history(tmp_history)
        results = search_history(path=tmp_history)
        assert len(results) == 0
