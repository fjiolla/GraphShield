"""
Graph builder — constructs a NetworkX graph from standardised records.

This module takes the output from any parser (node/edge records) and
builds a fully attributed NetworkX graph ready for analysis.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Build and summarise NetworkX graphs from raw record data."""

    def __init__(self, directed: bool = False) -> None:
        """Initialise the builder.

        Args:
            directed: If True, build a DiGraph; otherwise an undirected Graph.
        """
        self._directed = directed

    # ── Public API ───────────────────────────────────────────────────

    def build(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
    ) -> nx.Graph:
        """Construct a graph from node/edge records.

        Args:
            nodes: List of dicts — each must contain at least ``id``.
            edges: List of dicts — each must contain ``source`` and ``target``.

        Returns:
            A populated ``nx.Graph`` (or ``nx.DiGraph``).
        """
        G: nx.Graph = nx.DiGraph() if self._directed else nx.Graph()

        # Add nodes with attributes
        for node in nodes:
            node_id = str(node["id"])
            attrs = {k: v for k, v in node.items() if k != "id"}
            G.add_node(node_id, **attrs)

        # Add edges with attributes
        for edge in edges:
            src = str(edge["source"])
            tgt = str(edge["target"])
            attrs = {k: v for k, v in edge.items() if k not in ("source", "target")}
            G.add_edge(src, tgt, **attrs)

        logger.info(
            "Graph built — %d nodes, %d edges, directed=%s",
            G.number_of_nodes(),
            G.number_of_edges(),
            self._directed,
        )
        return G

    @staticmethod
    def get_summary(G: nx.Graph) -> dict[str, Any]:
        """Return a high-level summary of the graph.

        Returns:
            Dict with keys: node_count, edge_count, density,
            connected_components, is_directed, average_degree.
        """
        node_count = G.number_of_nodes()
        edge_count = G.number_of_edges()

        # Average degree
        if node_count > 0:
            avg_degree = round(sum(d for _, d in G.degree()) / node_count, 4)
        else:
            avg_degree = 0.0

        # Connected components (use weak for directed graphs)
        if G.is_directed():
            n_components = nx.number_weakly_connected_components(G)
        else:
            n_components = nx.number_connected_components(G)

        summary: dict[str, Any] = {
            "node_count": node_count,
            "edge_count": edge_count,
            "density": round(nx.density(G), 6),
            "connected_components": n_components,
            "is_directed": G.is_directed(),
            "average_degree": avg_degree,
        }

        # Group distribution (if a 'group' attribute exists)
        groups: dict[str, int] = {}
        for _, attrs in G.nodes(data=True):
            grp = str(attrs.get("group", "unknown"))
            groups[grp] = groups.get(grp, 0) + 1
        if groups:
            summary["group_distribution"] = groups

        logger.info("Graph summary: %s", summary)
        return summary
