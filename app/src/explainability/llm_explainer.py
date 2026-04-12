"""
LLM-powered explainability engine.

Takes bias metrics and a graph summary, constructs a detailed prompt,
sends it to Vertex AI, and parses the response into a structured
explanation.  Falls back to a template-based explanation when the LLM
is unavailable.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.src.services.gcp.vertex_ai_service import VertexAIService

logger = logging.getLogger(__name__)


class LLMExplainer:
    """Generate human-readable bias explanations using an LLM."""

    def __init__(
        self,
        # vertex_service: VertexAIService | None = None,
        # use_vertex_ai: bool = True,
        llm_service: Any | None = None,
        use_llm: bool = True,
        fallback_to_template: bool = True,
    ) -> None:
        # self._vertex = vertex_service
        # self._use_vertex = use_vertex_ai
        self._llm = llm_service
        self._use_llm = use_llm
        self._fallback = fallback_to_template

    # ── Public API ───────────────────────────────────────────────────

    def explain(
        self,
        bias_metrics: dict[str, Any],
        graph_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """Produce an explanation for detected bias.

        Args:
            bias_metrics: Combined output from all bias detectors.
            graph_summary: High-level stats about the graph.

        Returns:
            Dict with keys: ``explanation``, ``severity``,
            ``affected_groups``, ``contributing_factors``,
            ``confidence_score``.
        """
        # Try LLM first
        # if self._use_vertex and self._vertex and self._vertex.available:
        if self._use_llm and self._llm and self._llm.available:
            try:
                return self._explain_with_llm(bias_metrics, graph_summary)
            except Exception as exc:
                logger.warning("LLM explanation failed: %s", exc)
                if not self._fallback:
                    raise

        # Template fallback
        logger.info("Using template-based explanation (LLM unavailable).")
        return self._explain_with_template(bias_metrics, graph_summary)

    # ── LLM-based explanation ────────────────────────────────────────

    def _explain_with_llm(
        self,
        bias_metrics: dict[str, Any],
        graph_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """Call LLM to produce an explanation."""
        prompt = self._build_prompt(bias_metrics, graph_summary)
        # raw = self._vertex.generate_content(prompt)
        raw = self._llm.generate_content(prompt)  # type: ignore[union-attr]
        return self._parse_llm_response(raw, bias_metrics)

    @staticmethod
    def _build_prompt(
        bias_metrics: dict[str, Any],
        graph_summary: dict[str, Any],
    ) -> str:
        """Construct the LLM prompt."""
        return f"""You are an expert in graph fairness and bias analysis.

Given the following graph summary and bias detection results, provide a
detailed explanation in **valid JSON** matching this schema:

{{
  "explanation": "<A 3-5 sentence plain-English, non-technical explanation of the bias. Make sure a beginner can understand it.>",
  "severity": <integer 1-10>,
  "affected_groups": ["<group1>", "<group2>"],
  "contributing_factors": ["<factor1>", "<factor2>"],
  "mitigation_suggestions": ["<actionable step 1 to reduce bias>", "<actionable step 2>"],
  "confidence_score": <float 0.0-1.0>
}}

=== GRAPH SUMMARY ===
{json.dumps(graph_summary, indent=2)}

=== BIAS METRICS ===
{json.dumps(bias_metrics, indent=2, default=str)}

Rules:
- Explain WHY bias exists (or doesn't exist) in extremely simple, non-technical terms. If groups are missing, explain that they need to provide node attributes.
- Identify WHICH groups are most affected and how.
- You MUST include the "mitigation_suggestions" array field with clear, actionable steps on how to remove or mitigate these biases.
- Rate severity from 1 (negligible) to 10 (critical).
- List the key contributing factors (e.g., high homophily, centrality gap).
- Return ONLY valid JSON. No markdown fences or introduction text."""

    @staticmethod
    def _parse_llm_response(
        raw: str,
        bias_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract structured JSON from the LLM response."""
        # Strip markdown code fences if present
        cleaned = re.sub(r"```json\s*", "", raw)
        cleaned = re.sub(r"```\s*", "", cleaned)
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            # Validate minimum keys
            required = {"explanation", "severity", "confidence_score"}
            if required.issubset(parsed.keys()):
                if "mitigation_suggestions" not in parsed:
                    parsed["mitigation_suggestions"] = ["Ensure dataset representations are balanced.", "Evaluate network construction algorithms for disparity biases."]
                return parsed
        except json.JSONDecodeError:
            logger.warning("Could not parse LLM response as JSON.")

        # If parsing fails, wrap raw text as the explanation
        return {
            "explanation": raw.strip(),
            "severity": 5,
            "affected_groups": [],
            "contributing_factors": [],
            "mitigation_suggestions": [],
            "confidence_score": 0.5,
        }

    # ── Template-based fallback ──────────────────────────────────────

    @staticmethod
    def _explain_with_template(
        bias_metrics: dict[str, Any],
        graph_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a deterministic explanation without an LLM."""
        biased_areas: list[str] = []
        affected_groups: set[str] = set()
        contributing_factors: list[str] = []

        # Structural bias
        sb = bias_metrics.get("structural_bias", {})
        if sb.get("biased"):
            biased_areas.append("structural")
            contributing_factors.extend(
                f"Disparity in {m}" for m in sb.get("biased_metrics", [])
            )
            for metric_means in sb.get("group_means", {}).values():
                affected_groups.update(metric_means.keys())

        # Group fairness
        gf = bias_metrics.get("group_fairness", {})
        if gf.get("biased"):
            biased_areas.append("group fairness")
            for metric, di in gf.get("disparate_impact", {}).items():
                if di.get("biased_by_80_percent_rule"):
                    contributing_factors.append(
                        f"Disparate impact in {metric} "
                        f"(ratio={di.get('disparate_impact_ratio')})"
                    )

        # Edge bias
        eb = bias_metrics.get("edge_bias", {})
        if eb.get("biased"):
            biased_areas.append("edge connectivity")
            if eb.get("high_homophily"):
                contributing_factors.append(
                    f"High homophily (index={eb.get('homophily_index')})"
                )
            if eb.get("cross_group_disparity", 0) > 0.3:
                contributing_factors.append(
                    f"Cross-group connectivity disparity "
                    f"({eb.get('cross_group_disparity')})"
                )
            affected_groups.update(eb.get("group_cross_group_ratios", {}).keys())

        # Remove placeholder group names
        affected_groups.discard("unknown")

        # Build narrative
        if biased_areas:
            severity = min(3 + len(biased_areas) * 2 + len(contributing_factors), 10)
            confidence = round(0.6 + 0.1 * len(biased_areas), 2)
            explanation = (
                f"Bias was detected in the following areas: "
                f"{', '.join(biased_areas)}. "
                f"The graph has {graph_summary.get('node_count', '?')} nodes "
                f"and {graph_summary.get('edge_count', '?')} edges. "
                f"Key contributing factors include: "
                f"{'; '.join(contributing_factors) if contributing_factors else 'N/A'}. "
                f"Affected groups: {', '.join(sorted(affected_groups)) or 'N/A'}."
            )
        else:
            severity = 1
            confidence = 0.9
            explanation = (
                "No significant bias was detected across structural, "
                "group fairness, or edge connectivity dimensions."
            )

        return {
            "explanation": explanation,
            "severity": severity,
            "affected_groups": sorted(affected_groups),
            "contributing_factors": contributing_factors,
            "mitigation_suggestions": ["Provide a nodes dataset with specific group attributes to enable deeper fairness tracking rules."],
            "confidence_score": min(confidence, 1.0),
        }
