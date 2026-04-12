from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.src.ingestion.base_parser import BaseParser, EdgeRecord, NodeRecord

logger = logging.getLogger(__name__)


class JSONLDParser(BaseParser):
    """Parse a JSON-LD file into standardised node/edge records."""

    # Edge-like relationship keys we look for inside each JSON-LD entity.
    _RELATIONSHIP_KEYS = {"knows", "follows", "relatedTo", "connects", "link", "edge"}

    def parse(self, source: str) -> tuple[list[NodeRecord], list[EdgeRecord]]:
        """Read a ``.json`` / ``.jsonld`` file and return (nodes, edges).

        The file must contain either:
        - A top-level ``@graph`` array, **or**
        - A top-level ``nodes`` + ``edges`` structure, **or**
        - A flat array of entity objects.

        Args:
            source: Path to the JSON-LD file.

        Returns:
            Tuple of node dicts and edge dicts.
        """
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"JSON-LD file not found: {path}")

        logger.info("Parsing JSON-LD file: %s", path)
        with open(path, encoding="utf-8") as fh:
            data: dict | list = json.load(fh)

        nodes, edges = self._route(data)

        logger.info(
            "JSON-LD parsed — %d nodes, %d edges", len(nodes), len(edges)
        )
        return nodes, edges

    # ── Internal routing / extraction ─────────────────────────────────

    def _route(
        self, data: dict | list
    ) -> tuple[list[NodeRecord], list[EdgeRecord]]:
        """Decide which extraction strategy to use."""
        # Case 1: {"nodes": [...], "edges": [...]}
        if isinstance(data, dict) and "nodes" in data and "edges" in data:
            return self._from_explicit(data)

        # Case 2: {"@graph": [...]}
        if isinstance(data, dict) and "@graph" in data:
            return self._from_graph_array(data["@graph"])

        # Case 3: top-level array of entity objects
        if isinstance(data, list):
            return self._from_graph_array(data)

        raise ValueError(
            "JSON-LD structure not recognised. Expected '@graph', "
            "'nodes'+'edges', or a top-level array."
        )

    # -- Strategy: explicit nodes + edges keys --------------------------

    @staticmethod
    def _from_explicit(
        data: dict,
    ) -> tuple[list[NodeRecord], list[EdgeRecord]]:
        nodes: list[NodeRecord] = []
        for item in data["nodes"]:
            record: dict[str, Any] = {"id": str(item.get("@id", item.get("id")))}
            for k, v in item.items():
                if k not in ("@id", "id"):
                    record[k] = v
            nodes.append(record)

        edges: list[EdgeRecord] = []
        for item in data["edges"]:
            edges.append(
                {
                    "source": str(item.get("source", item.get("from"))),
                    "target": str(item.get("target", item.get("to"))),
                    **{
                        k: v
                        for k, v in item.items()
                        if k not in ("source", "target", "from", "to")
                    },
                }
            )
        return nodes, edges

    # -- Strategy: @graph array with embedded relationships -------------

    def _from_graph_array(
        self, items: list[dict],
    ) -> tuple[list[NodeRecord], list[EdgeRecord]]:
        nodes: list[NodeRecord] = []
        edges: list[EdgeRecord] = []

        for item in items:
            node_id = str(item.get("@id", item.get("id", id(item))))
            record: dict[str, Any] = {"id": node_id}

            for key, value in item.items():
                # Skip JSON-LD meta keys
                if key.startswith("@"):
                    continue

                # Detect relationship keys → edges
                if key in self._RELATIONSHIP_KEYS:
                    targets = value if isinstance(value, list) else [value]
                    for tgt in targets:
                        tgt_id = (
                            tgt.get("@id", tgt) if isinstance(tgt, dict) else tgt
                        )
                        edges.append(
                            {"source": node_id, "target": str(tgt_id)}
                        )
                else:
                    record[key] = value

            nodes.append(record)

        return nodes, edges
