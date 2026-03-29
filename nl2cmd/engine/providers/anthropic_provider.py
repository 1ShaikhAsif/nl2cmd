"""Anthropic Claude provider."""

from __future__ import annotations

from nl2cmd.engine.providers import BaseProvider, register


@register("anthropic")
class AnthropicProvider(BaseProvider):
    default_model = "claude-sonnet-4-20250514"
    env_key = "ANTHROPIC_API_KEY"

    def complete(self, system_prompt: str, user_message: str, model: str | None = None) -> str:
        from nl2cmd.config import get_api_key

        api_key = get_api_key("anthropic")
        if not api_key:
            raise EnvironmentError(
                "Anthropic API key not set.\n"
                "Set it with: nl2cmd config set anthropic_api_key YOUR_KEY\n"
                "Or: export ANTHROPIC_API_KEY='your-key'\n"
                "Or use --offline mode."
            )

        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Anthropic SDK not installed.\n"
                "Install with: pip install nl2cmd[anthropic]"
            )

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model or self.default_model,
            max_tokens=256,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return message.content[0].text.strip()
