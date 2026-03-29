"""AI engine — multi-provider LLM integration for command translation."""

from __future__ import annotations

from nl2cmd.distro import DistroInfo, detect_distro
from nl2cmd.engine.providers import get_provider, list_providers

# Default provider if none specified
DEFAULT_PROVIDER = "anthropic"


def translate(
    user_input: str,
    distro_info: DistroInfo | None = None,
    provider_name: str | None = None,
    model: str | None = None,
) -> str:
    """Translate natural language to a shell command using an LLM provider.

    Args:
        user_input: Natural language description.
        distro_info: Optional pre-detected distro info.
        provider_name: LLM provider ("anthropic", "openai", "gemini", "ollama", "groq").
        model: Specific model override. Uses provider default if not set.

    Returns:
        The generated command string.
    """
    if distro_info is None:
        distro_info = detect_distro()

    provider = get_provider(provider_name or DEFAULT_PROVIDER)
    return provider.translate(
        user_input=user_input,
        distro_name=distro_info.name,
        package_manager=distro_info.package_manager,
        model=model,
    )


def explain(
    command: str,
    provider_name: str | None = None,
    model: str | None = None,
) -> str:
    """Explain a shell command by breaking it down piece by piece.

    Args:
        command: The shell command to explain.
        provider_name: LLM provider to use.
        model: Specific model override.

    Returns:
        The explanation text.
    """
    provider = get_provider(provider_name or DEFAULT_PROVIDER)
    return provider.explain(command, model)
