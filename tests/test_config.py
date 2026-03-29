"""Tests for the config module."""

import os

import pytest

from nl2cmd import config


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Redirect config to a temp directory."""
    cfg_file = tmp_path / "config.yaml"
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_file)
    return cfg_file


class TestConfig:
    def test_load_empty(self, tmp_config):
        assert config.load() == {}

    def test_set_and_get(self, tmp_config):
        config.set_value("provider", "gemini")
        assert config.get("provider") == "gemini"

    def test_set_invalid_key(self, tmp_config):
        with pytest.raises(ValueError, match="Unknown config key"):
            config.set_value("invalid_key", "value")

    def test_set_api_key(self, tmp_config):
        config.set_value("openai_api_key", "sk-test-12345")
        assert config.get("openai_api_key") == "sk-test-12345"

    def test_delete(self, tmp_config):
        config.set_value("provider", "openai")
        assert config.delete("provider") is True
        assert config.get("provider") is None

    def test_delete_nonexistent(self, tmp_config):
        assert config.delete("provider") is False

    def test_reset(self, tmp_config):
        config.set_value("provider", "gemini")
        config.set_value("model", "gemini-2.5-pro")
        config.reset()
        assert config.load() == {}

    def test_multiple_values(self, tmp_config):
        config.set_value("provider", "groq")
        config.set_value("model", "llama-3.3-70b-versatile")
        config.set_value("groq_api_key", "gsk-test")
        data = config.load()
        assert data["provider"] == "groq"
        assert data["model"] == "llama-3.3-70b-versatile"
        assert data["groq_api_key"] == "gsk-test"

    def test_get_api_key_from_config(self, tmp_config, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        config.set_value("anthropic_api_key", "sk-ant-test")
        assert config.get_api_key("anthropic") == "sk-ant-test"

    def test_get_api_key_falls_back_to_env(self, tmp_config, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-test")
        assert config.get_api_key("openai") == "sk-env-test"

    def test_config_takes_precedence_over_env(self, tmp_config, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "env-key")
        config.set_value("gemini_api_key", "config-key")
        assert config.get_api_key("gemini") == "config-key"

    def test_get_api_key_none(self, tmp_config, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        assert config.get_api_key("groq") is None

    def test_get_ollama_host_default(self, tmp_config, monkeypatch):
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        assert config.get_ollama_host() == "http://localhost:11434"

    def test_get_ollama_host_from_config(self, tmp_config, monkeypatch):
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        config.set_value("ollama_host", "http://myserver:11434")
        assert config.get_ollama_host() == "http://myserver:11434"
