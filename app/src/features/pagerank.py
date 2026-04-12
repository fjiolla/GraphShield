"""
PageRank feature computation.

Wraps ``networkx.pagerank`` with configurable damping factor and
returns per-node scores.
"""

from __future__ import annotations

import logging

import networkx as nx

logger = logging.getLogger(__name__)


def compute_pagerank(
    G: nx.Graph,
    alpha: float = 0.85,
) -> dict[str, float]:
    """Compute PageRank for all nodes.

    Args:
        G: A NetworkX graph.
        alpha: Damping factor (default 0.85).

    Returns:
        Dict mapping node IDs to PageRank scores.
    """
    logger.info("Computing PageRank (alpha=%.2f) …", alpha)

    scores: dict[str, float] = nx.pagerank(G, alpha=alpha)

    logger.info("PageRank complete for %d nodes.", len(scores))
    return scores
