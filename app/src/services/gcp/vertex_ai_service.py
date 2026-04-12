"""
Google Vertex AI service.

Uses the modern ``google-genai`` SDK to call Gemini models on Vertex AI.
Falls back gracefully when credentials are unavailable.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class VertexAIService:
    """Thin wrapper around the Google Gen AI SDK for Vertex AI."""

    def __init__(
        self,
        project_id: str = "",
        location: str = "us-central1",
        model_name: str = "gemini-2.5-flash",
    ) -> None:
        self._project_id = project_id or os.getenv("GCP_PROJECT_ID", "")
        self._location = location
        self._model_name = model_name
        self._client: Optional[object] = None
        self._available: Optional[bool] = None

    # ── Public API ───────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """Return True if the Vertex AI client can be initialised."""
        if self._available is None:
            try:
                self._get_client()
                self._available = True
            except Exception:
                self._available = False
        return self._available

    def generate_content(self, prompt: str) -> str:
        """Send a prompt to the Vertex AI LLM and return the response text.

        Args:
            prompt: The text prompt to send.

        Returns:
            The model's response as a plain string.

        Raises:
            RuntimeError: If the client cannot be initialised.
        """
        client = self._get_client()
        logger.info("Sending prompt to Vertex AI (%s) …", self._model_name)

        response = client.models.generate_content(
            model=self._model_name,
            contents=prompt,
        )
        text = response.text
        logger.info("Received response from Vertex AI (%d chars).", len(text))
        return text

    # ── Internal ─────────────────────────────────────────────────────

    def _get_client(self) -> object:
        """Lazy-init the google-genai client."""
        if self._client is None:
            try:
                from google import genai  # type: ignore[import-untyped]

                self._client = genai.Client(
                    vertexai=True,
                    project=self._project_id,
                    location=self._location,
                )
                logger.info(
                    "Vertex AI client initialised (project=%s, location=%s).",
                    self._project_id,
                    self._location,
                )
            except Exception as exc:
                raise RuntimeError(
                    "Vertex AI client could not be initialised. "
                    "Ensure google-genai is installed and GCP credentials "
                    "are configured."
                ) from exc
        return self._client
