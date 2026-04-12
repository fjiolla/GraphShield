"""
Structural bias detection.

Compares centrality and PageRank distributions across groups defined
by a sensitive attribute.  A large disparity between group means
indicates structural bias in the graph topology.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)

# Disparity threshold — ratios below this are flagged as biased
_DEFAULT_THRESHOLD = 0.8


def detect_structural_bias(
    G: nx.Graph,
    centrality: dict[str, dict[str, float]],
    pagerank: dict[str, float],
    sensitive_attr: str = "group",
    threshold: float = _DEFAULT_THRESHOLD,
) -> dict[str, Any]:
    """Detect structural bias by comparing metric distributions across groups.

    Args:
        G: NetworkX graph with node attributes.
        centrality: Output of ``compute_centrality`` (degree + betweenness).
        pagerank: Output of ``compute_pagerank``.
        sensitive_attr: Node attribute key for group membership.
        threshold: Disparity ratio below which bias is flagged.

    Returns:
        Dict with per-metric group means, disparity ratios, and a
        boolean ``biased`` flag.
    """
    logger.info("Detecting structural bias …")

    # Partition nodes into groups
    groups: dict[str, list[str]] = {}
    for node, attrs in G.nodes(data=True):
        grp = str(attrs.get(sensitive_attr, "unknown"))
        groups.setdefault(grp, []).append(str(node))

    if len(groups) < 2:
        logger.warning("Fewer than 2 groups found — structural bias detection skipped.")
        return {"biased": False, "reason": "fewer_than_two_groups"}

    # Compute per-group means for each metric
    metrics_to_check = {
        "degree_centrality": centrality.get("degree_centrality", {}),
        "betweenness_centrality": centrality.get("betweenness_centrality", {}),
        "pagerank": pagerank,
    }

    group_means: dict[str, dict[str, float]] = {}
    disparity_ratios: dict[str, float] = {}
    biased_metrics: list[str] = []

    for metric_name, metric_vals in metrics_to_check.items():
        per_group: dict[str, float] = {}
        for grp, node_ids in groups.items():
            vals = [metric_vals.get(n, 0.0) for n in node_ids]
            per_group[grp] = round(float(np.mean(vals)), 6) if vals else 0.0
        group_means[metric_name] = per_group

        # Disparity ratio = min_group_mean / max_group_mean
        means = list(per_group.values())
        max_mean = max(means)
        min_mean = min(means)
        ratio = round(min_mean / max_mean, 6) if max_mean > 0 else 1.0
        disparity_ratios[metric_name] = ratio

        if ratio < threshold:
            biased_metrics.append(metric_name)

    is_biased = len(biased_metrics) > 0

    result: dict[str, Any] = {
        "biased": is_biased,
        "group_means": group_means,
        "disparity_ratios": disparity_ratios,
        "biased_metrics": biased_metrics,
        "threshold": threshold,
    }

    logger.info("Structural bias detected: %s  (biased_metrics=%s)", is_biased, biased_metrics)
    return result
