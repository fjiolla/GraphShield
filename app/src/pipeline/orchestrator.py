from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


load_dotenv()

from app.src.ingestion.base_parser import detect_format, get_parser
from app.src.graph.graph_builder import GraphBuilder
from app.src.features.centrality import compute_centrality
from app.src.features.pagerank import compute_pagerank
from app.src.features.community import compute_communities
from app.src.features.homophily import compute_homophily
from app.src.bias.structural_bias import detect_structural_bias
from app.src.bias.group_fairness import detect_group_fairness
from app.src.bias.edge_bias import detect_edge_bias
from app.src.explainability.llm_explainer import LLMExplainer
from app.src.services.gcp.storage_service import StorageService
from app.src.services.llm.groq_ai_service import GroqAIService

logger = logging.getLogger(__name__)

# Default config path (relative to project root)
_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"

def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load pipeline configuration from a YAML file.

    Falls back to built-in defaults if no file is found.
    """
    print(_DEFAULT_CONFIG)
    config_path = Path(path) if path else _DEFAULT_CONFIG
    if config_path.exists():
        with open(config_path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    logger.warning("Config file not found at %s — using defaults.", config_path)
    return {}


class PipelineOrchestrator:
    """End-to-end bias detection and explanation pipeline."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialise with optional config override.

        Args:
            config: Pipeline configuration dict.  If None, the default
                ``config.yaml`` is loaded.
        """
        self.config: dict[str, Any] = config or load_config()
        self._storage = StorageService(
            project_id=self.config.get("gcp", {}).get("project_id", ""),
            bucket_name=self.config.get("gcp", {}).get("bucket", ""),
        )
        # self._vertex = VerteGroqService(
        #     project_id=self.config.get("gcp", {}).get("project_id", ""),
        #     location=self.config.get("gcp", {}).get("location", "us-central1"),
        #     model_name=self.config.get("explainability", {}).get(
        #         "model_name", "gemini-2.5-flash"
        #     ),
        # )
        self._llm = GroqAIService(
            api_key=None,
            model_name=self.config.get("explainability", {}).get(
                "model_name", "llama-3.1-8b-instant"
            ),
        )

    # ── Full pipeline ────────────────────────────────────────────────

    def run(
        self,
        input_path: str,
        config_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute the complete pipeline.

        Args:
            input_path: Local file path or ``gs://`` URI.
            config_overrides: Optional dict merged on top of self.config.

        Returns:
            Full pipeline result dict.
        """
        cfg = {**self.config, **(config_overrides or {})}
        sensitive_attr = cfg.get("graph", {}).get("sensitive_attribute", "group")

        # Step 1 — Resolve input
        local_path = self._resolve_input(input_path)

        # Step 2 — Parse
        nodes_path = cfg.get("graph", {}).get("nodes_path")
        nodes, edges = self._parse(local_path, nodes_path=nodes_path)

        # Step 3 — Build graph
        directed = cfg.get("graph", {}).get("directed", False)
        builder = GraphBuilder(directed=directed)
        G = builder.build(nodes, edges)
        graph_summary = builder.get_summary(G)

        # Step 4 — Features
        features = self._compute_features(G, cfg, sensitive_attr)

        # Step 5 — Bias detection
        bias_metrics = self._detect_bias(G, features, cfg, sensitive_attr)

        # Step 6 — Explainability
        explanation_result = self._explain(bias_metrics, graph_summary, cfg)

        # Step 7 — Assemble output
        methods_used = self._list_methods(cfg)

        return {
            "graph_summary": graph_summary,
            "bias_metrics": bias_metrics,
            "explanation": {
                "summary": explanation_result.get("explanation", ""),
                "top_bias_drivers": [
                    {
                        "factor": factor,
                        "description": factor,
                        "severity": "high" if explanation_result.get("severity", 0) > 7 else "medium"
                    }
                    for factor in explanation_result.get("contributing_factors", [])
                ],
            },
            "severity": explanation_result.get("severity", 0),
            "affected_groups": explanation_result.get("affected_groups", []),
            "contributing_factors": explanation_result.get("contributing_factors", []),
            "mitigation_suggestions": explanation_result.get("mitigation_suggestions", []),
            "confidence_score": explanation_result.get("confidence_score", 0.0),
            "methods_used": methods_used,
            "features": {
                "centrality_sample_size": len(
                    features.get("centrality", {}).get("degree_centrality", {})
                ),
                "communities_detected": len(
                    set(features.get("community", {}).values())
                )
                if features.get("community")
                else 0,
                "homophily": features.get("homophily", {}),
            },
        }

    # ── Sub-pipelines (for partial / testing runs) ───────────────────

    def run_bias_only(
        self,
        input_path: str,
        config_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run ingestion → features → bias detection (no explainability)."""
        cfg = {**self.config, **(config_overrides or {})}
        sensitive_attr = cfg.get("graph", {}).get("sensitive_attribute", "group")

        local_path = self._resolve_input(input_path)
        nodes, edges = self._parse(local_path)
        directed = cfg.get("graph", {}).get("directed", False)
        G = GraphBuilder(directed=directed).build(nodes, edges)
        features = self._compute_features(G, cfg, sensitive_attr)
        bias_metrics = self._detect_bias(G, features, cfg, sensitive_attr)

        return {"bias_metrics": bias_metrics}

    def run_explain_only(
        self,
        bias_metrics: dict[str, Any],
        graph_summary: dict[str, Any],
        config_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run only the explainability step with pre-computed metrics."""
        cfg = {**self.config, **(config_overrides or {})}
        return self._explain(bias_metrics, graph_summary, cfg)

    # ── Internal steps ───────────────────────────────────────────────

    def _resolve_input(self, input_path: str) -> str:
        """Download from GCS if needed, otherwise return local path."""
        if self._storage.is_gs_path(input_path):
            logger.info("Fetching file from GCS: %s", input_path)
            return self._storage.download(input_path)
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        return input_path

    @staticmethod
    def _parse(local_path: str, nodes_path: str | None = None) -> tuple[list[dict], list[dict]]:
        """Detect format and parse the file."""
        fmt = detect_format(local_path)
        if fmt == "csv" and nodes_path:
            from app.src.ingestion.csv_parser import CSVParser
            parser = CSVParser(nodes_path=nodes_path)
        else:
            parser = get_parser(fmt)
        return parser.parse(local_path)

    @staticmethod
    def _compute_features(
        G: "nx.Graph",  # noqa: F821
        cfg: dict[str, Any],
        sensitive_attr: str,
    ) -> dict[str, Any]:
        """Compute all feature metrics."""
        damping = cfg.get("pagerank", {}).get("damping_factors", [0.85])[0]
        resolution = cfg.get("community", {}).get("resolutions", [1.0])[0]

        centrality = compute_centrality(G)
        pagerank = compute_pagerank(G, alpha=damping)
        community = compute_communities(G, resolution=resolution)
        homophily = compute_homophily(G, sensitive_attr=sensitive_attr)

        return {
            "centrality": centrality,
            "pagerank": pagerank,
            "community": community,
            "homophily": homophily,
        }

    @staticmethod
    def _detect_bias(
        G: "nx.Graph",  # noqa: F821
        features: dict[str, Any],
        cfg: dict[str, Any],
        sensitive_attr: str,
    ) -> dict[str, Any]:
        """Run enabled bias detectors."""
        bias_cfg = cfg.get("bias_methods", {})
        result: dict[str, Any] = {}

        if bias_cfg.get("structural", True):
            result["structural_bias"] = detect_structural_bias(
                G,
                centrality=features["centrality"],
                pagerank=features["pagerank"],
                sensitive_attr=sensitive_attr,
            )

        if bias_cfg.get("fairness", True):
            result["group_fairness"] = detect_group_fairness(
                G,
                centrality=features["centrality"],
                sensitive_attr=sensitive_attr,
            )

        if bias_cfg.get("edge", True):
            result["edge_bias"] = detect_edge_bias(
                G,
                homophily=features["homophily"],
                sensitive_attr=sensitive_attr,
            )

        return result

    def _explain(
        self,
        bias_metrics: dict[str, Any],
        graph_summary: dict[str, Any],
        cfg: dict[str, Any],
    ) -> dict[str, Any]:
        """Produce an explanation using LLM or template."""
        exp_cfg = cfg.get("explainability", {})
        # explainer = LLMExplainer(
        #     vertex_service=self._vertex,
        #     use_vertex_ai=exp_cfg.get("use_vertex_ai", True),
        #     fallback_to_template=exp_cfg.get("fallback_to_template", True),
        # )
        explainer = LLMExplainer(
            llm_service=self._llm,
            use_llm=exp_cfg.get("use_groq_ai", True),
            fallback_to_template=exp_cfg.get("fallback_to_template", True),
        )
        return explainer.explain(bias_metrics, graph_summary)

    @staticmethod
    def _list_methods(cfg: dict[str, Any]) -> list[str]:
        """Build the list of methods used for the output payload."""
        methods: list[str] = []
        bias_cfg = cfg.get("bias_methods", {})
        if bias_cfg.get("structural", True):
            methods.append("structural_bias_detection")
        if bias_cfg.get("fairness", True):
            methods.append("group_fairness_analysis")
        if bias_cfg.get("edge", True):
            methods.append("edge_bias_analysis")
        exp_cfg = cfg.get("explainability", {})
        # if exp_cfg.get("use_vertex_ai", True):
        #     methods.append("vertex_ai_llm_explanation")
        if exp_cfg.get("use_groq_ai", True):
            methods.append("groq_ai_llm_explanation")
        else:
            methods.append("template_explanation")
        return methods


# ── Standalone execution ─────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys

    from src.services.gcp.logging_service import setup_logging

    setup_logging()

    if len(sys.argv) < 2:
        print("Usage: python -m src.pipeline.orchestrator <input_path> [config_path]")
        sys.exit(1)

    input_file = sys.argv[1]
    cfg_path = sys.argv[2] if len(sys.argv) > 2 else None

    config = load_config(cfg_path)
    orchestrator = PipelineOrchestrator(config)
    result = orchestrator.run(input_file)

    print(json.dumps(result, indent=2, default=str))
