"""
Google Cloud Storage service.

Provides a simple interface to download files from GCS buckets.
Falls back gracefully when credentials are not available.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class StorageService:
    """Wrapper around Google Cloud Storage for file downloads."""

    def __init__(self, project_id: str = "", bucket_name: str = "") -> None:
        self._project_id = project_id or os.getenv("GCP_PROJECT_ID", "")
        self._bucket_name = bucket_name or os.getenv("GCP_BUCKET", "")
        self._client: Optional[object] = None

    # ── Public API ───────────────────────────────────────────────────

    def download(self, gs_path: str, local_dir: str | None = None) -> str:
        """Download a file from GCS and return the local path.

        Args:
            gs_path: GCS URI in the format ``gs://bucket/path/to/file``.
            local_dir: Directory to save the file in.  Defaults to a
                temp directory.

        Returns:
            Absolute path to the downloaded file.

        Raises:
            RuntimeError: If GCS is not available.
            ValueError: If *gs_path* is not a valid GCS URI.
        """
        bucket_name, blob_path = self._parse_gs_uri(gs_path)
        filename = Path(blob_path).name

        if local_dir is None:
            local_dir = tempfile.mkdtemp(prefix="pipeline_")
        local_path = os.path.join(local_dir, filename)

        client = self._get_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        logger.info("Downloading gs://%s/%s → %s", bucket_name, blob_path, local_path)
        blob.download_to_filename(local_path)

        return local_path

    def is_gs_path(self, path: str) -> bool:
        """Check whether *path* is a GCS URI."""
        return path.strip().startswith("gs://")

    # ── Internal helpers ─────────────────────────────────────────────

    def _get_client(self) -> object:
        """Lazy-initialise the GCS client."""
        if self._client is None:
            try:
                from google.cloud import storage  # type: ignore[import-untyped]

                self._client = storage.Client(project=self._project_id or None)
                logger.info("GCS client initialised (project=%s).", self._project_id)
            except Exception as exc:
                raise RuntimeError(
                    "Google Cloud Storage client could not be initialised. "
                    "Make sure google-cloud-storage is installed and "
                    "credentials are configured."
                ) from exc
        return self._client

    @staticmethod
    def _parse_gs_uri(gs_path: str) -> tuple[str, str]:
        """Split ``gs://bucket/path`` into (bucket, path)."""
        if not gs_path.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gs_path}")
        parts = gs_path[5:].split("/", 1)
        if len(parts) < 2 or not parts[1]:
            raise ValueError(f"GCS URI must include a blob path: {gs_path}")
        return parts[0], parts[1]
