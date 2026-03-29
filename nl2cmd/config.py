"""Persistent configuration stored in ~/.nl2cmd/config.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path.home() / ".nl2cmd"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Valid config keys and their descriptions
CONFIG_KEYS: dict[str, str] = {
    "provider": "Default LLM provider (anthropic, openai, gemini, ollama, groq)",
    "model": "Default model name (e.g. gpt-4o, llama3.2, gemini-2.0-flash)",
    "anthropic_api_key": "Anthropic API key",
    "openai_api_key": "OpenAI API key",
    "gemini_api_key": "Google Gemini API key",
    "groq_api_key": "Groq API key",
    "ollama_host": "Ollama server URL (default: http://localhost:11434)",
}

# Map config keys to environment variable names
CONFIG_TO_ENV: dict[str, str] = {
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "gemini_api_key": "GEMINI_API_KEY",
    "groq_api_key": "GROQ_API_KEY",
    "ollama_host": "OLLAMA_HOST",
}

# Provider name -> config key for its API key
PROVIDER_KEY_MAP: dict[str, str] = {
    "anthropic": "anthropic_api_key",
    "openai": "openai_api_key",
    "gemini": "gemini_api_key",
    "groq": "groq_api_key",
}


def _ensure_dir() -> None:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load() -> dict[str, Any]:
    """Load config from disk. Returns empty dict if no config exists."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        data = yaml.safe_load(CONFIG_FILE.read_text())
        return data if isinstance(data, dict) else {}
    except (yaml.YAMLError, OSError):
        return {}


def save(config: dict[str, Any]) -> None:
    """Save config to disk."""
    _ensure_dir()
    CONFIG_FILE.write_text(yaml.dump(config, default_flow_style=False, sort_keys=True))


def get(key: str, default: Any = None) -> Any:
    """Get a single config value."""
    return load().get(key, default)


def set_value(key: str, value: str) -> None:
    """Set a single config value."""
    if key not in CONFIG_KEYS:
        valid = ", ".join(sorted(CONFIG_KEYS.keys()))
        raise ValueError(f"Unknown config key '{key}'. Valid keys: {valid}")
    config = load()
    config[key] = value
    save(config)


def delete(key: str) -> bool:
    """Delete a config key. Returns True if key existed."""
    config = load()
    if key in config:
        del config[key]
        save(config)
        return True
    return False


def reset() -> None:
    """Delete all config."""
    save({})


def get_api_key(provider_name: str) -> str | None:
    """Get API key for a provider — checks config first, then env var."""
    import os

    config_key = PROVIDER_KEY_MAP.get(provider_name)
    if not config_key:
        return None

    # Config file takes precedence
    value = get(config_key)
    if value:
        return value

    # Fall back to environment variable
    env_var = CONFIG_TO_ENV.get(config_key, "")
    return os.environ.get(env_var) or None


def get_ollama_host() -> str:
    """Get Ollama host — checks config first, then env var, then default."""
    import os

    return (
        get("ollama_host")
        or os.environ.get("OLLAMA_HOST")
        or "http://localhost:11434"
    )
