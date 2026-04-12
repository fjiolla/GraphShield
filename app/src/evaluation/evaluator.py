"""
Multi-parameter evaluation module.

Sweeps over configurable parameter ranges (e.g. PageRank damping
factors, Louvain resolutions) and collects per-experiment bias
detection results.  Returns the experiment set ranked by confidence.
"""

from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from app.src.features.centrality import compute_centrality
from app.src.features.pagerank import compute_pagerank
from app.src.features.community import compute_communities
from app.src.features.homophily import compute_homophily
from app.src.bias.structural_bias import detect_structural_bias
from app.src.bias.group_fairness import detect_group_fairness
from app.src.bias.edge_bias import detect_edge_bias
from app.src.explainability.llm_explainer import LLMExplainer

logger = logging.getLogger(__name__)


@dataclass
class ExperimentResult:
    """Container for one experiment's parameters and results."""

    params: dict[str, float]
    bias_metrics: dict[str, Any]
    explanation: dict[str, Any]
    confidence_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "params": self.params,
            "bias_metrics": self.bias_metrics,
            "explanation": self.explanation,
            "confidence_score": self.confidence_score,
        }


class Evaluator:
    """Run multi-parameter experiments on a graph."""

    def __init__(
        self,
        explainer: LLMExplainer | None = None,
    ) -> None:
        self._explainer = explainer or LLMExplainer(
            use_vertex_ai=False,
            fallback_to_template=True,
        )

    def run_experiments(
        self,
        G: nx.Graph,
        graph_summary: dict[str, Any],
        config: dict[str, Any],
    ) -> list[ExperimentResult]:
        """Sweep over parameter combinations and collect results.

        The parameter space is defined by:
        - ``config["pagerank"]["damping_factors"]`` — list of floats
        - ``config["community"]["resolutions"]`` — list of floats

        Args:
            G: The constructed graph.
            graph_summary: Output of ``GraphBuilder.get_summary``.
            config: Pipeline configuration dict.

        Returns:
            List of ``ExperimentResult`` objects sorted best-first
            (highest confidence first).
        """
        sensitive_attr = config.get("graph", {}).get("sensitive_attribute", "group")
        damping_factors = config.get("pagerank", {}).get("damping_factors", [0.85])
        resolutions = config.get("community", {}).get("resolutions", [1.0])

        combos = list(itertools.product(damping_factors, resolutions))
        logger.info(
            "Running %d experiments (%d damping × %d resolution).",
            len(combos),
            len(damping_factors),
            len(resolutions),
        )

        results: list[ExperimentResult] = []

        for alpha, resolution in combos:
            logger.info("Experiment: alpha=%.3f, resolution=%.2f", alpha, resolution)

            # Features
            centrality = compute_centrality(G)
            pagerank = compute_pagerank(G, alpha=alpha)
            _communities = compute_communities(G, resolution=resolution)
            homophily = compute_homophily(G, sensitive_attr=sensitive_attr)

            # Bias detection
            bias_metrics: dict[str, Any] = {}
            bias_cfg = config.get("bias_methods", {})

            if bias_cfg.get("structural", True):
                bias_metrics["structural_bias"] = detect_structural_bias(
                    G, centrality, pagerank, sensitive_attr=sensitive_attr,
                )
            if bias_cfg.get("fairness", True):
                bias_metrics["group_fairness"] = detect_group_fairness(
                    G, centrality, sensitive_attr=sensitive_attr,
                )
            if bias_cfg.get("edge", True):
                bias_metrics["edge_bias"] = detect_edge_bias(
                    G, homophily, sensitive_attr=sensitive_attr,
                )

            # Explanation
            explanation = self._explainer.explain(bias_metrics, graph_summary)
            confidence = explanation.get("confidence_score", 0.0)

            results.append(
                ExperimentResult(
                    params={"damping_factor": alpha, "resolution": resolution},
                    bias_metrics=bias_metrics,
                    explanation=explanation,
                    confidence_score=confidence,
                )
            )

        # Sort by confidence descending
        results.sort(key=lambda r: r.confidence_score, reverse=True)
        logger.info(
            "Best experiment: params=%s, confidence=%.3f",
            results[0].params if results else {},
            results[0].confidence_score if results else 0.0,
        )
        return results
