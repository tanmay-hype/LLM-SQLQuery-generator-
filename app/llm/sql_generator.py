from typing import Callable, Optional

import httpx

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover - optional dependency at import time
    genai = None
    genai_types = None

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency at import time
    OpenAI = None


class SQLGenerator:
    """Handles communication with the LLM."""

    def __init__(self):
        self.gemini_client = (
            genai.Client(api_key=GEMINI_API_KEY)
            if genai is not None and GEMINI_API_KEY
            else None
        )
        self.openai_client = (
            OpenAI(api_key=OPENAI_API_KEY)
            if OpenAI is not None and OPENAI_API_KEY
            else None
        )
        self.http_client = httpx.Client(timeout=60.0)

    def generate_sql(self, prompt: str) -> str:
        providers: list[tuple[str, Callable[[str], str]]] = []

        if self.gemini_client is not None:
            providers.append(("gemini", self._generate_with_gemini))

        if self.openai_client is not None:
            providers.append(("openai", self._generate_with_openai))

        providers.append(("ollama", self._generate_with_ollama))

        last_error: Exception | None = None

        for _provider_name, provider in providers:
            try:
                sql = provider(prompt)
                if sql:
                    return self._clean_sql(sql)
            except Exception as exc:
                last_error = exc

        if last_error is not None:
            raise last_error

        raise RuntimeError("No LLM provider is configured.")

    def _generate_with_gemini(self, prompt: str) -> str:
        if self.gemini_client is None or genai_types is None:
            raise ImportError("Gemini provider is not available.")

        response = self.gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0,
            ),
        )

        return getattr(response, "text", "") or ""

    def _generate_with_openai(self, prompt: str) -> str:
        if self.openai_client is None:
            raise ImportError("OpenAI provider is not available.")

        response = self.openai_client.responses.create(
            model=OPENAI_MODEL,
            input=prompt,
            temperature=0,
        )

        return response.output_text or ""

    def _generate_with_ollama(self, prompt: str) -> str:
        response = self.http_client.post(
            f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                },
            },
        )
        response.raise_for_status()

        data = response.json()
        return data.get("response", "") or ""

    @staticmethod
    def _clean_sql(sql: str) -> str:
        """
        Remove markdown formatting if the model returns it.
        """

        sql = sql.replace("```sql", "")
        sql = sql.replace("```", "")

        return sql.strip()