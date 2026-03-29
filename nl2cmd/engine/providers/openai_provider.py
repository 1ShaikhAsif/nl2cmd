"""OpenAI GPT provider."""

from __future__ import annotations

from nl2cmd.engine.providers import BaseProvider, register


@register("openai")
class OpenAIProvider(BaseProvider):
    default_model = "gpt-4o"
    env_key = "OPENAI_API_KEY"

    def complete(self, system_prompt: str, user_message: str, model: str | None = None) -> str:
        from nl2cmd.config import get_api_key

        api_key = get_api_key("openai")
        if not api_key:
            raise EnvironmentError(
                "OpenAI API key not set.\n"
                "Set it with: nl2cmd config set openai_api_key YOUR_KEY\n"
                "Or: export OPENAI_API_KEY='your-key'\n"
                "Or use --offline mode."
            )

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed.\n"
                "Install with: pip install nl2cmd[openai]"
            )

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model or self.default_model,
            max_tokens=256,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content.strip()
