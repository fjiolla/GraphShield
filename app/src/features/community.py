"""
Community detection via the Louvain algorithm.

Uses the native ``networkx.algorithms.community.louvain_communities``
implementation with configurable resolution.
"""

from __future__ import annotations

import logging

import networkx as nx
from networkx.algorithms.community import louvain_communities

logger = logging.getLogger(__name__)


def compute_communities(
    G: nx.Graph,
    resolution: float = 1.0,
    seed: int = 42,
) -> dict[str, int]:
    """Assign each node to a community using Louvain.

    Args:
        G: A NetworkX graph (undirected).
        resolution: Louvain resolution parameter. Values > 1 favour
            smaller communities; values < 1 favour larger ones.
        seed: Random seed for reproducibility.

    Returns:
        Dict mapping node IDs to community indices (0-based).
    """
    logger.info(
        "Running Louvain community detection (resolution=%.2f) …",
        resolution,
    )

    # louvain_communities returns a list of frozensets
    work_graph = G.to_undirected() if G.is_directed() else G

    communities = louvain_communities(work_graph, resolution=resolution, seed=seed)

    # Flatten into a node → community_id mapping
    mapping: dict[str, int] = {}
    for idx, community_set in enumerate(communities):
        for node in community_set:
            mapping[str(node)] = idx

    logger.info("Detected %d communities across %d nodes.", len(communities), len(mapping))
    return mapping
