"""Tests for the CLI interface."""

from click.testing import CliRunner

from nl2cmd.cli import main


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def test_version(self):
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "nl2cmd" in result.output

    def test_help(self):
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "nl2cmd" in result.output.lower()

    def test_no_args(self):
        result = self.runner.invoke(main, [])
        assert result.exit_code == 0

    def test_dry_mode_offline(self):
        result = self.runner.invoke(main, ["--dry", "--offline", "show", "open", "ports"])
        assert result.exit_code == 0
        assert "ss" in result.output

    def test_dry_disk_usage(self):
        result = self.runner.invoke(main, ["--dry", "--offline", "disk", "usage", "by", "size"])
        assert result.exit_code == 0
        assert "du" in result.output

    def test_offline_no_match(self):
        result = self.runner.invoke(
            main,
            ["--offline", "completely random gibberish xyz"],
        )
        assert result.exit_code != 0


class TestConfigCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def test_config_help(self):
        result = self.runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0
        assert "config" in result.output.lower()

    def test_config_show(self):
        result = self.runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0

    def test_config_path(self):
        result = self.runner.invoke(main, ["config", "path"])
        assert result.exit_code == 0
        assert ".nl2cmd" in result.output

    def test_config_providers(self):
        result = self.runner.invoke(main, ["config", "providers"])
        assert result.exit_code == 0
        assert "anthropic" in result.output
        assert "ollama" in result.output
        assert "gemini" in result.output
