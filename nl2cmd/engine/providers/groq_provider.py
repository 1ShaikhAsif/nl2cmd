"""Groq provider — fast cloud inference for Meta Llama, Mixtral, Gemma, etc."""

from __future__ import annotations

from nl2cmd.engine.providers import BaseProvider, register


@register("groq")
class GroqProvider(BaseProvider):
    default_model = "llama-3.3-70b-versatile"
    env_key = "GROQ_API_KEY"

    def complete(self, system_prompt: str, user_message: str, model: str | None = None) -> str:
        from nl2cmd.config import get_api_key

        api_key = get_api_key("groq")
        if not api_key:
            raise EnvironmentError(
                "Groq API key not set.\n"
                "Set it with: nl2cmd config set groq_api_key YOUR_KEY\n"
                "Or: export GROQ_API_KEY='your-key'\n"
                "Get a free key at: https://console.groq.com\n"
                "Or use --offline mode."
            )

        try:
            from groq import Groq
        except ImportError:
            raise ImportError(
                "Groq SDK not installed.\n"
                "Install with: pip install nl2cmd[groq]"
            )

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model or self.default_model,
            max_tokens=256,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content.strip()
