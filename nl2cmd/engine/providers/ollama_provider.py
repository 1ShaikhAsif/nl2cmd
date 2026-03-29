"""Ollama provider — local open-source models (Llama 3, Mistral, Phi, Qwen, etc.)."""

from __future__ import annotations

from nl2cmd.engine.providers import BaseProvider, register


@register("ollama")
class OllamaProvider(BaseProvider):
    default_model = "llama3.2"
    env_key = "OLLAMA_HOST"

    def complete(self, system_prompt: str, user_message: str, model: str | None = None) -> str:
        try:
            import ollama as ollama_sdk
        except ImportError:
            raise ImportError(
                "Ollama SDK not installed.\n"
                "Install with: pip install nl2cmd[ollama]\n"
                "Also install Ollama: https://ollama.com"
            )

        from nl2cmd.config import get_ollama_host

        host = get_ollama_host()
        client = ollama_sdk.Client(host=host)

        response = client.chat(
            model=model or self.default_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.message.content.strip()
