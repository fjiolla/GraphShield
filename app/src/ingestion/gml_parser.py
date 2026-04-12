"""
GML file parser.

Uses networkx.read_gml to load the graph, then extracts nodes and edges
into the standardised record format.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import networkx as nx

from app.src.ingestion.base_parser import BaseParser, EdgeRecord, NodeRecord

logger = logging.getLogger(__name__)


class GMLParser(BaseParser):
    """Parse a GML file into standardised node/edge records."""

    def parse(self, source: str) -> tuple[list[NodeRecord], list[EdgeRecord]]:
        """Read a ``.gml`` file and return (nodes, edges).

        Args:
            source: Absolute or relative path to a ``.gml`` file.

        Returns:
            Tuple of node dicts and edge dicts.
        """
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"GML file not found: {path}")

        logger.info("Parsing GML file: %s", path)
        graph: nx.Graph = nx.read_gml(str(path))

        nodes = self._extract_nodes(graph)
        edges = self._extract_edges(graph)

        logger.info(
            "GML parsed — %d nodes, %d edges", len(nodes), len(edges)
        )
        return nodes, edges

    # ── Internal helpers ─────────────────────────────────────────────

    @staticmethod
    def _extract_nodes(graph: nx.Graph) -> list[NodeRecord]:
        """Extract nodes with all their attributes."""
        nodes: list[NodeRecord] = []
        for node_id, attrs in graph.nodes(data=True):
            record: dict[str, Any] = {"id": str(node_id)}
            record.update(attrs)
            nodes.append(record)
        return nodes

    @staticmethod
    def _extract_edges(graph: nx.Graph) -> list[EdgeRecord]:
        """Extract edges with all their attributes."""
        edges: list[EdgeRecord] = []
        for src, tgt, attrs in graph.edges(data=True):
            record: dict[str, Any] = {
                "source": str(src),
                "target": str(tgt),
            }
            record.update(attrs)
            edges.append(record)
        return edges
