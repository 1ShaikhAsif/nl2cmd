"""LLM provider abstraction — swap providers with a single config change."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

SYSTEM_PROMPT_TEMPLATE = """You are a Linux command translator running on {distro}.

RULES:
1. Output ONLY the shell command. No explanation, no markdown,
   no backticks, no commentary.
2. If multiple commands are needed, chain with && or |
3. Use the correct package manager for this distro:
   {package_manager}
4. Prefer standard coreutils over third-party tools
5. If the request is ambiguous, output the safest interpretation
6. Never output commands that would:
   - Delete system files without explicit request
   - Run as root unless clearly needed
   - Download and pipe to shell (curl | bash)
7. For destructive operations, use --interactive or -i flags
   where available"""

EXPLAIN_PROMPT = """You are a Linux command explainer.

Given a command, break it down piece by piece. For each part, show:
  part → what it does

Be concise and precise. Output plain text, no markdown.
Example format:
  find /var/log       → search in /var/log directory
  -name "*.log"       → match files ending in .log"""


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    name: str
    model: str
    api_key: str = ""
    base_url: str = ""


class BaseProvider(ABC):
    """Abstract base class for all LLM providers."""

    name: str = ""
    default_model: str = ""
    env_key: str = ""  # e.g. ANTHROPIC_API_KEY

    @abstractmethod
    def complete(self, system_prompt: str, user_message: str, model: str | None = None) -> str:
        """Send a prompt and return the text response."""

    def translate(self, user_input: str, distro_name: str, package_manager: str, model: str | None = None) -> str:
        """Translate natural language to a shell command."""
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            distro=distro_name,
            package_manager=package_manager,
        )
        response = self.complete(system_prompt, user_input, model)
        return _clean_command(response)

    def explain(self, command: str, model: str | None = None) -> str:
        """Explain a shell command."""
        return self.complete(EXPLAIN_PROMPT, f"Explain this command: {command}", model)


def _clean_command(text: str) -> str:
    """Strip markdown artifacts from LLM response."""
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
        if text.startswith("bash\n") or text.startswith("sh\n"):
            text = text.split("\n", 1)[1].strip()
    if text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    if text.startswith("$ "):
        text = text[2:]
    return text


# --- Provider registry ---

_PROVIDERS: dict[str, type[BaseProvider]] = {}


def register(name: str):
    """Decorator to register a provider class."""
    def decorator(cls: type[BaseProvider]):
        cls.name = name
        _PROVIDERS[name] = cls
        return cls
    return decorator


def get_provider(name: str) -> BaseProvider:
    """Get a provider instance by name. Raises ValueError if unknown or missing SDK."""
    if name not in _PROVIDERS:
        available = ", ".join(sorted(_PROVIDERS.keys()))
        raise ValueError(f"Unknown provider '{name}'. Available: {available}")
    return _PROVIDERS[name]()


def list_providers() -> list[str]:
    """Return all registered provider names."""
    return sorted(_PROVIDERS.keys())


# Import all provider modules to trigger registration
from nl2cmd.engine.providers import (  # noqa: E402, F401
    anthropic_provider,
    openai_provider,
    gemini_provider,
    ollama_provider,
    groq_provider,
)
