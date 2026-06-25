"""OpenAI-compatible LLM client for the Affiliate Strategy suite.

Connects to any OpenAI-compatible API endpoint (OpenAI, OpenRouter,
Ollama, LM Studio, etc.) via environment variables. No mock, no fallback.
"""

import os
from openai import OpenAI


class OpenAIClient:
    """LLM client that calls an OpenAI-compatible API.

    Requires the following environment variables:
        OPENAI_API_KEY  — Your API key.
        OPENAI_API_BASE — The base URL of the API endpoint.
        OPENAI_MODEL    — (Optional) Model identifier. Defaults to 'gpt-4o-mini'.
    """

    def __init__(self) -> None:
        """Initialize the client, reading config from environment variables.

        Raises:
            EnvironmentError: If required environment variables are not set.
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        api_base = os.environ.get("OPENAI_API_BASE")

        missing = []
        if not api_key:
            missing.append("OPENAI_API_KEY")
        if not api_base:
            missing.append("OPENAI_API_BASE")

        if missing:
            raise EnvironmentError(
                f"Missing required environment variable(s): {', '.join(missing)}\n\n"
                "Set them before running:\n"
                "  export OPENAI_API_BASE=https://api.openai.com/v1\n"
                "  export OPENAI_API_KEY=sk-your-key-here\n"
                "  export OPENAI_MODEL=gpt-4o-mini  # optional\n"
            )

        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=api_key, base_url=api_base)

    def generate(self, prompt: str) -> str:
        """Generate a text completion for the given prompt.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            The generated text response.

        Raises:
            RuntimeError: If the API call fails.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("LLM returned empty response.")
            return content.strip()
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            raise RuntimeError(f"LLM API call failed: {e}") from e
