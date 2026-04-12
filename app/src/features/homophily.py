"""
Homophily index computation.

Homophily measures the tendency of nodes to connect with similar nodes
(those sharing the same value of a sensitive / group attribute).

Index = (# same-group edges) / (# total edges)
  - 1.0 = perfect homophily (all edges within groups)
  - 0.0 = perfect heterophily (all edges across groups)
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


def compute_homophily(
    G: nx.Graph,
    sensitive_attr: str = "group",
) -> dict[str, Any]:
    """Compute the homophily index and per-group breakdown.

    Args:
        G: A NetworkX graph whose nodes have *sensitive_attr* set.
        sensitive_attr: Node attribute key representing group membership.

    Returns:
        Dict containing:
        - ``homophily_index``: float between 0 and 1.
        - ``same_group_edges``: count of intra-group edges.
        - ``cross_group_edges``: count of inter-group edges.
        - ``total_edges``: total edge count.
    """
    logger.info("Computing homophily index (attr='%s') …", sensitive_attr)

    same_group = 0
    cross_group = 0

    for u, v in G.edges():
        u_group = G.nodes[u].get(sensitive_attr, "unknown")
        v_group = G.nodes[v].get(sensitive_attr, "unknown")
        if u_group == v_group:
            same_group += 1
        else:
            cross_group += 1

    total = same_group + cross_group
    index = round(same_group / total, 6) if total > 0 else 0.0

    result = {
        "homophily_index": index,
        "same_group_edges": same_group,
        "cross_group_edges": cross_group,
        "total_edges": total,
    }

    logger.info("Homophily result: %s", result)
    return result
