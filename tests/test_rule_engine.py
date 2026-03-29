"""Tests for the rule engine."""

from pathlib import Path

import pytest

from nl2cmd.engine.rule_engine import Rule, SlotDef, load_rules, match_input


@pytest.fixture
def rules():
    """Load bundled rules for testing."""
    return load_rules()


class TestLoadRules:
    def test_loads_bundled_rules(self, rules):
        assert len(rules) > 0

    def test_rules_have_required_fields(self, rules):
        for rule in rules:
            assert rule.intent
            assert rule.patterns
            assert rule.command

    def test_no_duplicate_intents(self, rules):
        intents = [r.intent for r in rules]
        assert len(intents) == len(set(intents))


class TestExactMatch:
    def test_find_large_files(self, rules):
        result = match_input("find large files over 1gb", rules)
        assert result.matched
        assert "1G" in result.command

    def test_show_open_ports(self, rules):
        result = match_input("show open ports", rules)
        assert result.matched
        assert "ss" in result.command

    def test_disk_usage(self, rules):
        result = match_input("disk usage by folder", rules)
        assert result.matched
        assert "du" in result.command

    def test_git_undo(self, rules):
        result = match_input("undo last commit", rules)
        assert result.matched
        assert "git reset" in result.command

    def test_kill_port(self, rules):
        result = match_input("kill process on port 3000", rules)
        assert result.matched
        assert "3000" in result.command

    def test_docker_stop_all(self, rules):
        result = match_input("stop all containers", rules)
        assert result.matched
        assert "docker stop" in result.command

    def test_count_lines(self, rules):
        result = match_input("count lines in README.md", rules)
        assert result.matched
        assert "wc -l" in result.command

    def test_git_status(self, rules):
        result = match_input("git status", rules)
        assert result.matched
        assert "git status" in result.command


class TestFuzzyMatch:
    def test_typo_tolerance(self, rules):
        result = match_input("shwo open prots", rules)
        assert result.matched

    def test_word_reorder(self, rules):
        result = match_input("ports that are listening", rules)
        assert result.matched

    def test_no_match_garbage(self, rules):
        result = match_input("asdfjkl random nonsense xyz", rules)
        assert not result.matched


class TestSlotExtraction:
    def test_filesize_parsing(self, rules):
        result = match_input("find large files over 500mb", rules)
        assert result.matched
        assert "500M" in result.command

    def test_port_extraction(self, rules):
        result = match_input("kill process on port 8080", rules)
        assert result.matched
        assert "8080" in result.command

    def test_default_values(self, rules):
        result = match_input("find large files over 100M", rules)
        assert result.matched
