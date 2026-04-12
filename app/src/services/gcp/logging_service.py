"""
Logging service.

Sets up structured logging that works with Google Cloud Logging when
credentials are available, and falls back to Python stdlib logging
otherwise.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(
    level: int = logging.INFO,
    use_cloud_logging: bool = True,
) -> None:
    """Configure application-wide logging.

    Args:
        level: Python log level (e.g. ``logging.INFO``).
        use_cloud_logging: If True, attempt to attach Google Cloud
            Logging.  Falls back to console logging on failure.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if root.handlers:
        return

    # Try Google Cloud Logging first
    if use_cloud_logging:
        try:
            import google.cloud.logging as cloud_logging  # type: ignore[import-untyped]

            client = cloud_logging.Client()
            client.setup_logging(log_level=level)
            root.info("Google Cloud Logging attached.")
            return
        except Exception:
            pass  # Fall through to stdlib logging

    # Fallback: console handler with a readable format
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
