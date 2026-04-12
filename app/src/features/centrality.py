"""
Centrality feature computation.

Computes degree centrality and betweenness centrality for every node
in the graph and returns the results as a dictionary.
"""

from __future__ import annotations

import logging

import networkx as nx

logger = logging.getLogger(__name__)


def compute_centrality(G: nx.Graph) -> dict[str, dict[str, float]]:
    """Compute degree and betweenness centrality for all nodes.

    Args:
        G: A NetworkX graph.

    Returns:
        Dict with keys ``degree_centrality`` and ``betweenness_centrality``,
        each mapping node IDs to their centrality value.
    """
    logger.info("Computing centrality metrics …")

    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)

    logger.info("Centrality computation complete for %d nodes.", G.number_of_nodes())
    return {
        "degree_centrality": degree,
        "betweenness_centrality": betweenness,
    }
