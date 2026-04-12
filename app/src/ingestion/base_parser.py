from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)




NodeRecord = dict[str, Any]   # {"id": ..., "group": ..., ...}
EdgeRecord = dict[str, Any]   # {"source": ..., "target": ..., "weight": ...}


class BaseParser(ABC):
    """Abstract base class for all graph data parsers."""

    @abstractmethod
    def parse(self, source: str) -> tuple[list[NodeRecord], list[EdgeRecord]]:
        """Parse *source* (file path or raw string) into nodes and edges.

        Returns:
            A tuple of (nodes_list, edges_list) where each element is a dict
            containing at minimum ``id`` for nodes and ``source``/``target``
            for edges.
        """

    # Convenience helper shared by all parsers
    @staticmethod
    def _ensure_id(node: dict, fallback_key: str = "label") -> dict:
        """Guarantee every node dict has an ``id`` key."""
        if "id" not in node:
            node["id"] = node.get(fallback_key, id(node))
        return node


# ── Format detection ─────────────────────────────────────────────────

_FORMAT_MAP: dict[str, str] = {
    ".gml": "gml",
    ".json": "jsonld",
    ".jsonld": "jsonld",
    ".csv": "csv",
}


def detect_format(path: str) -> str:
    """Return format identifier (``gml``, ``jsonld``, ``csv``) based on extension.

    Raises:
        ValueError: If the extension is not recognised.
    """
    ext = Path(path).suffix.lower()
    fmt = _FORMAT_MAP.get(ext)
    if fmt is None:
        raise ValueError(
            f"Unsupported file extension '{ext}'. "
            f"Supported: {list(_FORMAT_MAP.keys())}"
        )
    logger.info("Detected format '%s' for path: %s", fmt, path)
    return fmt


def get_parser(format_name: str) -> BaseParser:
    """Factory — return the correct parser instance for *format_name*.

    Imports are deferred so each parser module stays independently loadable.
    """
    # Lazy imports to avoid circular dependencies
    if format_name == "gml":
        from app.src.ingestion.gml_parser import GMLParser
        return GMLParser()
    if format_name == "jsonld":
        from app.src.ingestion.jsonld_parser import JSONLDParser
        return JSONLDParser()
    if format_name == "csv":
        from app.src.ingestion.csv_parser import CSVParser
        return CSVParser()
    raise ValueError(f"No parser registered for format '{format_name}'")
