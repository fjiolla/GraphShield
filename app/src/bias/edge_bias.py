"""
Edge bias detection.

Analyses the distribution of edges between and within groups to detect
connectivity-level bias.  High homophily (most edges stay within the
same group) or asymmetric cross-group connectivity can indicate edge-
level bias.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


def detect_edge_bias(
    G: nx.Graph,
    homophily: dict[str, Any],
    sensitive_attr: str = "group",
    homophily_threshold: float = 0.8,
) -> dict[str, Any]:
    """Detect edge-level bias via homophily and cross-group connectivity.

    Args:
        G: NetworkX graph with group attributes on nodes.
        homophily: Output of ``compute_homophily``.
        sensitive_attr: Key for the group attribute.
        homophily_threshold: Homophily index above which the graph is
            considered biased (i.e., edges are disproportionately
            intra-group).

    Returns:
        Dict with homophily analysis, cross-group connectivity
        breakdown, and a ``biased`` flag.
    """
    logger.info("Detecting edge bias …")

    # --- 1. Homophily bias ------------------------------------------------

    homophily_index = homophily.get("homophily_index", 0.0)
    high_homophily = homophily_index >= homophily_threshold

    # --- 2. Cross-group connectivity breakdown ----------------------------
    # Count edges between every pair of groups

    groups: dict[str, list[str]] = {}
    for node, attrs in G.nodes(data=True):
        grp = str(attrs.get(sensitive_attr, "unknown"))
        groups.setdefault(grp, []).append(str(node))

    pair_counts: dict[str, int] = {}
    for u, v in G.edges():
        u_grp = str(G.nodes[u].get(sensitive_attr, "unknown"))
        v_grp = str(G.nodes[v].get(sensitive_attr, "unknown"))
        pair_key = f"{min(u_grp, v_grp)} <-> {max(u_grp, v_grp)}"
        pair_counts[pair_key] = pair_counts.get(pair_key, 0) + 1

    # --- 3. Connectivity disparity ----------------------------------------
    # For each group, compute the fraction of its edges that go cross-group

    group_cross_ratios: dict[str, float] = {}
    for grp, node_ids in groups.items():
        node_set = set(node_ids)
        total = 0
        cross = 0
        for node in node_ids:
            for neighbor in G.neighbors(node):
                total += 1
                if str(neighbor) not in node_set:
                    cross += 1
        group_cross_ratios[grp] = round(cross / total, 6) if total > 0 else 0.0

    # Disparity in cross-group ratios across groups
    ratios = list(group_cross_ratios.values())
    cross_disparity = round(max(ratios) - min(ratios), 6) if ratios else 0.0

    # Flag as biased if homophily is high OR cross-group disparity is large
    is_biased = high_homophily or cross_disparity > 0.3

    result: dict[str, Any] = {
        "biased": is_biased,
        "homophily_index": homophily_index,
        "high_homophily": high_homophily,
        "homophily_threshold": homophily_threshold,
        "edge_pair_counts": pair_counts,
        "group_cross_group_ratios": group_cross_ratios,
        "cross_group_disparity": cross_disparity,
    }

    logger.info("Edge bias detected: %s", is_biased)
    return result
