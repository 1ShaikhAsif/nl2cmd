"""Hybrid engine — rules first, AI fallback."""

from __future__ import annotations

from dataclasses import dataclass

from nl2cmd.distro import DistroInfo, detect_distro
from nl2cmd.engine.ai_engine import translate as ai_translate
from nl2cmd.engine.rule_engine import MatchResult, load_rules, match_input


@dataclass
class TranslationResult:
    """Result from the hybrid translation engine."""

    command: str
    source: str  # "rule" or "ai"
    rule_intent: str | None = None
    score: float = 0.0


def translate(
    user_input: str,
    offline: bool = False,
    distro_info: DistroInfo | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> TranslationResult:
    """Translate natural language to a shell command.

    Tries rules first. If no match and not offline, falls back to AI.

    Args:
        user_input: The natural language description.
        offline: If True, only use rule engine (no API calls).
        distro_info: Optional pre-detected distro info.
        provider: LLM provider name override.
        model: Specific model override for the provider.

    Returns:
        TranslationResult with the command and its source.

    Raises:
        ValueError: If no rule match found in offline mode.
        EnvironmentError: If AI fallback fails (no API key).
    """
    if distro_info is None:
        distro_info = detect_distro()

    # Always try rules first
    rules = load_rules()
    result: MatchResult = match_input(user_input, rules)

    if result.matched:
        return TranslationResult(
            command=result.command,
            source="rule",
            rule_intent=result.rule.intent if result.rule else None,
            score=result.score,
        )

    if offline:
        raise ValueError(
            "No matching rule found. Remove --offline to allow AI fallback."
        )

    # Fallback to AI
    command = ai_translate(user_input, distro_info, provider_name=provider, model=model)
    return TranslationResult(command=command, source="ai")
