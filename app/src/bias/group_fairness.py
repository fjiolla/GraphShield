"""
Group fairness bias detection.

Implements two classical fairness measures applied to graph-structural
metrics:

1. **Statistical Parity Difference** — the difference in mean metric
   value between the most- and least-advantaged groups.
2. **Disparate Impact Ratio** — the ratio of favourable metric rates
   between the unprivileged and privileged groups.

A perfectly fair graph would have SPD = 0 and DIR = 1.0.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)


def detect_group_fairness(
    G: nx.Graph,
    centrality: dict[str, dict[str, float]],
    sensitive_attr: str = "group",
    positive_threshold: float | None = None,
) -> dict[str, Any]:
    """Evaluate group fairness on centrality metrics.

    Args:
        G: NetworkX graph with group attributes on nodes.
        centrality: Output from ``compute_centrality``.
        sensitive_attr: Key for the group attribute.
        positive_threshold: Centrality value above which a node is
            considered to have a "positive outcome".  If None, the
            median of each metric is used.

    Returns:
        Dict with ``statistical_parity`` and ``disparate_impact``
        results, plus an overall ``biased`` flag.
    """
    logger.info("Detecting group fairness bias …")

    # Partition nodes into groups
    groups: dict[str, list[str]] = {}
    for node, attrs in G.nodes(data=True):
        grp = str(attrs.get(sensitive_attr, "unknown"))
        groups.setdefault(grp, []).append(str(node))

    if len(groups) < 2:
        logger.warning("Fewer than 2 groups — group fairness skipped.")
        return {"biased": False, "reason": "fewer_than_two_groups"}

    sp_results: dict[str, dict[str, Any]] = {}
    di_results: dict[str, dict[str, Any]] = {}
    any_biased = False

    for metric_name, metric_vals in centrality.items():
        all_values = list(metric_vals.values())
        threshold = (
            positive_threshold
            if positive_threshold is not None
            else float(np.median(all_values))
        )

        # Positive-outcome rate per group
        group_rates: dict[str, float] = {}
        for grp, node_ids in groups.items():
            vals = [metric_vals.get(n, 0.0) for n in node_ids]
            positive_count = sum(1 for v in vals if v >= threshold)
            rate = positive_count / len(vals) if vals else 0.0
            group_rates[grp] = round(rate, 6)

        rates = list(group_rates.values())
        max_rate = max(rates)
        min_rate = min(rates)

        # Statistical parity difference
        spd = round(max_rate - min_rate, 6)

        # Disparate impact ratio
        dir_value = round(min_rate / max_rate, 6) if max_rate > 0 else 1.0

        # The 80% rule: DIR < 0.8 is considered biased
        metric_biased = dir_value < 0.8

        sp_results[metric_name] = {
            "group_positive_rates": group_rates,
            "statistical_parity_difference": spd,
            "threshold_used": round(threshold, 6),
        }
        di_results[metric_name] = {
            "disparate_impact_ratio": dir_value,
            "biased_by_80_percent_rule": metric_biased,
        }

        if metric_biased:
            any_biased = True

    result: dict[str, Any] = {
        "biased": any_biased,
        "statistical_parity": sp_results,
        "disparate_impact": di_results,
    }

    logger.info("Group fairness bias detected: %s", any_biased)
    return result
