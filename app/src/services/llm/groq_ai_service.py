"""
Groq AI service.

Uses standard HTTP requests to `api.groq.com` (OpenAI-compatible) to call Groq models.
"""

from __future__ import annotations

import json
import logging
import os

import requests

logger = logging.getLogger(__name__)


class GroqAIService:
    """Wrapper around Groq AI (Groq) using standard HTTP requests."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "groq-beta",
    ) -> None:
        """Initialise the Groq AI client.

        Args:
            api_key: The Groq API key. If not provided, it will be mapped to the
                GROQ_API_KEY environment variable.
            model_name: The name of the Groq model to use (default: groq-beta).
        """
        self._api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self._model_name = model_name
        self._api_url = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def available(self) -> bool:
        """Return True if the Groq API credentials are mathematically available."""
        if not self._api_key:
            logger.warning("Groq AI unavailable: GROQ_API_KEY is missing.")
            return False
        return True

    def generate_content(self, prompt: str) -> str:
        """Send a prompt to the Groq LLM and return the response text.

        Args:
            prompt: the complete prompt.

        Returns:
            The raw string response from Groq AI.
        """
        if not self.available:
            raise RuntimeError("Groq AI client is not correctly configured.")

        logger.info("Sending prompt to Groq AI (%s) …", self._model_name)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        payload = {
            "model": self._model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            # If using groq-2 or others, temperature and the rest can be modified here
            "temperature": 0.0,
            "stream": False,
        }

        try:
            response = requests.post(
                self._api_url, headers=headers, json=payload, timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            # Extract content from the first choice
            text = data.get("choices", [])[0].get("message", {}).get("content", "")
            
            logger.info("Received response from Groq AI (%d chars).", len(text))
            return text
            
        except requests.exceptions.RequestException as exc:
            logger.error("Groq AI request failed: %s", exc)
            if hasattr(exc, 'response') and exc.response is not None:
                logger.error("Response body: %s", exc.response.text)
            raise RuntimeError(f"Groq AI request failed: {exc}") from exc
