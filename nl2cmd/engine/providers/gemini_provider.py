"""Google Gemini provider."""

from __future__ import annotations

from nl2cmd.engine.providers import BaseProvider, register


@register("gemini")
class GeminiProvider(BaseProvider):
    default_model = "gemini-2.0-flash"
    env_key = "GEMINI_API_KEY"

    def complete(self, system_prompt: str, user_message: str, model: str | None = None) -> str:
        from nl2cmd.config import get_api_key

        api_key = get_api_key("gemini")
        if not api_key:
            raise EnvironmentError(
                "Gemini API key not set.\n"
                "Set it with: nl2cmd config set gemini_api_key YOUR_KEY\n"
                "Or: export GEMINI_API_KEY='your-key'\n"
                "Or use --offline mode."
            )

        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "Google GenAI SDK not installed.\n"
                "Install with: pip install nl2cmd[gemini]"
            )

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model or self.default_model,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=256,
            ),
            contents=user_message,
        )
        return response.text.strip()
