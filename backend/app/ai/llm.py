"""LLM Client: OpenRouter chat completions over HTTPX with retries.

The OpenRouter API key is provided through InsForge: `insforge ai setup`
writes it to the local server-side env file as OPENROUTER_API_KEY. It is
never logged or echoed back. Missing keys raise a clear LLMError.
"""

import asyncio
import json

import httpx
from loguru import logger

from app.core.config import get_settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/auto"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 60.0
RETRY_BACKOFF_SECONDS = 2.0
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class LLMError(Exception):
    """Raised when the LLM cannot be reached or its output cannot be parsed."""


def _extract_json(content: str) -> dict:
    """Parse a JSON object out of the model reply, tolerating markdown fences."""
    text = content.strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.startswith("```")]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMError("LLM response did not contain a JSON object")

    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM response was not valid JSON: {exc}") from exc


class LLMClient:
    """Minimal OpenRouter chat client."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = TIMEOUT_SECONDS,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL or DEFAULT_MODEL
        self.timeout = timeout
        self.max_retries = max_retries

    def is_configured(self) -> bool:
        """True when an OpenRouter API key is available."""
        return bool(self.api_key)

    async def chat_json(self, messages: list[dict]) -> dict:
        """Send a chat request and return the parsed JSON object from the model."""
        if not self.is_configured():
            raise LLMError("OPENROUTER_API_KEY is not set. Run `insforge ai setup` to configure it.")

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await client.post(OPENROUTER_BASE_URL, headers=headers, json=payload)

                    if response.status_code == 400 and "response_format" in payload:
                        # Some models do not support JSON mode; retry without it.
                        logger.warning("model rejected response_format; retrying without it")
                        payload.pop("response_format")
                        continue

                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return _extract_json(content)

                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                        logger.warning("OpenRouter HTTP {} (attempt {})", exc.response.status_code, attempt)
                        await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
                        continue
                    raise LLMError(f"OpenRouter returned HTTP {exc.response.status_code}") from exc
                except httpx.RequestError as exc:
                    if attempt < self.max_retries:
                        logger.warning("OpenRouter request failed (attempt {}): {}", attempt, exc)
                        await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
                        continue
                    raise LLMError(f"OpenRouter request failed: {exc}") from exc
                except (KeyError, IndexError) as exc:
                    raise LLMError("Unexpected OpenRouter response shape") from exc

            raise LLMError("OpenRouter request failed after retries")
