"""
struct_reporting.py
Module 4: Explainability & Reporting
Uses Groq to generate narrative text for a fairness report.
Deterministic structure (metrics, dataset_overview) is built in Python.
Groq generates: summary, column_explanations, explanations, recommendations, research_grounding.

Output: Strict JSON (Looker Studio-ready), no markdown formatting.
"""

import json
import logging
import re
import textwrap
from collections import defaultdict
from typing import Optional

from app.core.struct_local_config import struct_get_groq_client, GROQ_MODEL_NAME, GROQ_TEMPERATURE

struct_logger = logging.getLogger("struct_reporting")

# Hard caps for response size control
MAX_SUMMARY_COLUMN_PAIRS = 20        # Max column pairs in metrics_summary
MAX_DETAILED_METRICS_PER_COLUMN = 5  # Top worst groups per column pair
# Total max metrics entries = 20 × 5 = 100


# ─────────────────────────────────────────────
# Report Schema (Looker Studio–ready)
# ─────────────────────────────────────────────
STRUCT_REPORT_SCHEMA = {
    "summary": "str — Executive summary of findings",
    "bias_detected": "bool",
    "risk_level": "str — High | Medium | Low | None",
    "dataset_overview": {
        "table_name": "str",
        "total_rows": "int",
        "target_columns": "list[str]",
        "sensitive_columns": "list[str]",
        "proxy_columns": "list[str]",
    },
    "column_explanations": {
        "<column_name>": {
            "type": "str",
            "reason": "str — detailed explanation",
            "bias_risk_explanation": "str — specific risk",
        }
    },
    "metrics_summary": {
        "<target_col>.<sensitive_col>": {
            "total_flagged_groups": "int",
            "worst_disparate_impact_ratio": "float",
            "worst_statistical_parity_difference": "float",
            "privileged_group": "str",
        }
    },
    "metrics": {
        "<target_col>.<sensitive_col>.<group>": {
            "disparate_impact_ratio": "float | null",
            "statistical_parity_difference": "float | null",
            "privileged_group": "str",
            "unprivileged_group": "str",
            "flagged": "bool",
            "interpretation": "str",
        }
    },
    "explanations": {
        "disparate_impact": "str",
        "statistical_parity": "str",
        "proxy_risk": "str",
    },
    "recommendations": ["list of actionable steps — fully dynamic from Groq"],
    "research_grounding": {
        "reference": "str — dynamic citation from Groq",
        "applicability": "str — dynamic applicability from Groq",
    },
    "looker_studio_ready": True,
}


# ─────────────────────────────────────────────
# Metrics Serialization (compact, for Groq prompt)
# ─────────────────────────────────────────────
def struct_serialize_metrics_for_prompt(
    audit_result: dict,
    column_classification: dict,
) -> str:
    """
    Build a compact summary of audit data for the Groq narrative prompt.
    Only includes essential info needed for generating explanations.
    """
    flagged_pairs = audit_result.get("flagged_pairs", [])
    top_flagged = flagged_pairs[:10]

    compact = {
        "table": audit_result.get("table"),
        "rows": audit_result.get("total_rows"),
        "bias_detected": audit_result.get("bias_detected"),
        "targets": audit_result.get("target_columns"),
        "sensitive": audit_result.get("sensitive_columns"),
        "proxies": audit_result.get("proxy_columns"),
        "flagged_count": len(flagged_pairs),
        "top_flagged": [
            {
                "target": p.get("target_column"),
                "sensitive": p.get("sensitive_column"),
                "group": p.get("unprivileged_group"),
                "dir": p.get("disparate_impact_ratio"),
                "spd": p.get("statistical_parity_difference"),
            }
            for p in top_flagged
        ],
        "columns": {
            col: meta.get("type")
            for col, meta in column_classification.items()
        },
    }

    return json.dumps(compact, separators=(',', ':'), default=str)


# ─────────────────────────────────────────────
# Groq Narrative Prompt
# ─────────────────────────────────────────────
def struct_build_report_prompt(metrics_json: str) -> str:
    """
    Build a compact prompt asking Groq for ALL narrative text fields.
    Structural data (metrics, dataset_overview) is built in Python.
    Groq provides: summary, column_explanations, explanations,
    recommendations, research_grounding.
    """
    prompt = textwrap.dedent(f"""
    Analyze this bias audit data and return ONLY valid JSON with these exact keys:

    1. "summary": string, 2-3 sentence executive summary of the bias findings.

    2. "column_explanations": object mapping EVERY column name to:
       {{"type":"Target|Sensitive|Proxy|Safe",
         "reason":"Detailed 1-2 sentence explanation of why this column was classified this way, referencing the data characteristics.",
         "bias_risk_explanation":"Specific 1-2 sentence explanation of the bias risk this column poses to model fairness."}}

    3. "explanations": object with exactly these 3 keys:
       "disparate_impact": what the DIR findings mean for this specific dataset,
       "statistical_parity": what the SPD findings mean for this specific dataset,
       "proxy_risk": how the identified proxy columns could introduce hidden discrimination in this dataset.

    4. "recommendations": array of 4+ specific, actionable recommendations grounded in fairness research (e.g., Mehrabi et al., 2021 and related works), but STRICTLY tailored to the dataset findings.Each recommendation MUST:- Be directly linked to a detected issue in the dataset- Mention the affected column(s)- Specify the type of bias (e.g., gender bias, class imbalance, proxy bias)- Describe the observed problem (e.g., skewed distribution, imbalance, correlation)- Provide a concrete, implementable solution (e.g., re-sampling, re-weighting, feature removal, transformation)Avoid generic statements. Every recommendation must be dataset-specific and based only on the audit results.

    5. "research_grounding": object with:
       "reference": full academic citation of the primary reference used,
       "applicability": 2-3 sentences explaining how the referenced research applies to these specific audit findings.

    Context: DIR<0.8 = bias (EEOC 4/5ths rule). |SPD|>0.1 = bias. Proxy = indirect discrimination via correlated features.

    DATA: {metrics_json}

    Return ONLY a valid JSON object. No markdown, no code fences, no preamble.
    """).strip()

    return prompt


# ─────────────────────────────────────────────
# Build Deterministic Report Structure
# ─────────────────────────────────────────────
def struct_build_deterministic_report(
    audit_result: dict,
    column_classification: dict,
    narrative: dict,
) -> dict:
    """
    Build the final report by combining:
    - Deterministic data (metrics, dataset_overview) computed in Python
    - Narrative text (summary, explanations, recommendations, etc.) from Groq
    The response schema is guaranteed correct regardless of LLM behavior.
    """
    bias_detected = audit_result.get("bias_detected", False)
    flagged_pairs = audit_result.get("flagged_pairs", [])

    # Risk level
    if not flagged_pairs:
        risk_level = "None"
    elif len(flagged_pairs) > 3:
        risk_level = "High"
    else:
        risk_level = "Medium"

    # ── Group flagged pairs by target.sensitive ──
    grouped = defaultdict(list)
    for pair in flagged_pairs:
        col_key = f"{pair['target_column']}.{pair['sensitive_column']}"
        grouped[col_key].append(pair)

    # ── Metrics Summary (column-level aggregation, sorted by worst DIR) ──
    all_summaries = []
    for col_key, pairs in grouped.items():
        dirs = [p.get("disparate_impact_ratio") for p in pairs if p.get("disparate_impact_ratio") is not None]
        spds = [p.get("statistical_parity_difference") for p in pairs if p.get("statistical_parity_difference") is not None]
        worst_dir = min(dirs) if dirs else None
        worst_spd = max(spds, key=abs) if spds else None

        all_summaries.append((col_key, {
            "total_flagged_groups": len(pairs),
            "worst_disparate_impact_ratio": round(worst_dir, 6) if worst_dir is not None else None,
            "worst_statistical_parity_difference": round(worst_spd, 6) if worst_spd is not None else None,
            "privileged_group": pairs[0].get("privileged_group") if pairs else None,
        }))

    # Sort by worst DIR ascending (most biased first), cap at MAX_SUMMARY_COLUMN_PAIRS
    all_summaries.sort(key=lambda x: x[1]["worst_disparate_impact_ratio"] if x[1]["worst_disparate_impact_ratio"] is not None else float('inf'))
    top_column_pairs = all_summaries[:MAX_SUMMARY_COLUMN_PAIRS]

    metrics_summary = {col_key: summary for col_key, summary in top_column_pairs}

    # ── Detailed Metrics (top 5 worst groups per selected column pair) ──
    selected_col_keys = {col_key for col_key, _ in top_column_pairs}
    metrics = {}
    for col_key in selected_col_keys:
        pairs = grouped[col_key]
        # Sort by DIR ascending (worst = lowest DIR first)
        sorted_pairs = sorted(
            pairs,
            key=lambda p: p.get("disparate_impact_ratio") if p.get("disparate_impact_ratio") is not None else float('inf')
        )
        for pair in sorted_pairs[:MAX_DETAILED_METRICS_PER_COLUMN]:
            detail_key = f"{pair['target_column']}.{pair['sensitive_column']}.{pair['unprivileged_group']}"
            metrics[detail_key] = {
                "disparate_impact_ratio": pair.get("disparate_impact_ratio"),
                "statistical_parity_difference": pair.get("statistical_parity_difference"),
                "privileged_group": pair.get("privileged_group"),
                "unprivileged_group": pair.get("unprivileged_group"),
                "flagged": True,
                "interpretation": f"This group violated the threshold: {pair.get('threshold_violated')}.",
            }

    # ── Column Explanations (from Groq narrative, with classification type enforced) ──
    groq_col_explanations = narrative.get("column_explanations", {})
    column_explanations = {}
    for col, meta in column_classification.items():
        col_type = meta.get("type", "Safe")
        groq_entry = groq_col_explanations.get(col, {})

        if isinstance(groq_entry, dict) and groq_entry.get("reason"):
            reason = groq_entry["reason"]
            bias_risk = groq_entry.get("bias_risk_explanation",
                f"This column was classified as {col_type} and may pose bias risk."
                if col_type in ("Sensitive", "Proxy")
                else "Low bias risk."
            )
        else:
            # Fallback: use classification reason from intelligence module
            reason = meta.get("reason", f"Column '{col}' classified as {col_type}.")
            bias_risk = (
                f"This column was flagged as a {col_type} risk factor."
                if col_type in ("Sensitive", "Proxy")
                else "Low bias risk."
            )

        column_explanations[col] = {
            "type": col_type,
            "reason": reason,
            "bias_risk_explanation": bias_risk,
        }

    # ── Summary (from Groq) ──
    summary = narrative.get("summary")
    if not summary or not isinstance(summary, str):
        summary = (
            f"Automated audit of table '{audit_result.get('table')}' "
            f"({audit_result.get('total_rows')} rows) found "
            f"{'bias violations' if bias_detected else 'no significant bias violations'}. "
            f"{len(flagged_pairs)} group pairs were flagged."
        )

    # ── Explanations (from Groq) ──
    explanations = narrative.get("explanations", {})
    if not isinstance(explanations, dict) or len(explanations) < 3:
        explanations = {
            "disparate_impact": (
                "Disparate Impact Ratio measures how proportionally different the positive "
                "outcome rates are between groups. Values below 0.8 violate the EEOC 4/5ths rule."
            ),
            "statistical_parity": (
                "Statistical Parity Difference measures the absolute gap in outcome rates. "
                "Values above ±0.1 indicate meaningful disparity between groups."
            ),
            "proxy_risk": (
                "Proxy features appear neutral but correlate with sensitive attributes, "
                "enabling indirect discrimination (e.g., Zip_Code correlating with Race "
                "due to residential segregation patterns)."
            ),
        }

    # ── Recommendations (from Groq — fully dynamic) ──
    recommendations = narrative.get("recommendations", [])
    if not recommendations or not isinstance(recommendations, list) or len(recommendations) < 3:
        # Minimal fallback only if Groq completely failed
        recommendations = [
            f"Review the {len(flagged_pairs)} flagged group pairs for potential discrimination patterns.",
            "Apply fairness-aware preprocessing techniques such as reweighting or resampling to mitigate identified disparities.",
            "Conduct intersectional analysis to understand how multiple sensitive attributes interact to produce compounded bias.",
            "Establish ongoing monitoring of model outputs by demographic group to detect emerging bias in production.",
        ]

    # ── Research Grounding (from Groq — fully dynamic) ──
    research_grounding = narrative.get("research_grounding", {})
    if not isinstance(research_grounding, dict) or not research_grounding.get("reference"):
        # Minimal fallback only if Groq completely failed
        research_grounding = {
            "reference": (
                "Mehrabi, N., Morstatter, F., Saxena, N., Lerman, K., & Galstyan, A. (2021). "
                "A Survey on Bias and Fairness in Machine Learning. "
                "ACM Computing Surveys, 54(6), 1–35. https://doi.org/10.1145/3457607"
            ),
            "applicability": (
                f"The audit of table '{audit_result.get('table')}' identified {len(flagged_pairs)} "
                f"flagged group pairs across {len(grouped)} sensitive column combinations. "
                "The DIR and SPD metrics used align with the group fairness definitions in Mehrabi et al. Section 3."
            ),
        }

    # ── Assemble final report ──
    return {
        "summary": summary,
        "bias_detected": bias_detected,
        "risk_level": risk_level,
        "dataset_overview": {
            "table_name": audit_result.get("table"),
            "total_rows": audit_result.get("total_rows"),
            "target_columns": audit_result.get("target_columns", []),
            "sensitive_columns": audit_result.get("sensitive_columns", []),
            "proxy_columns": audit_result.get("proxy_columns", []),
        },
        "column_explanations": column_explanations,
        "metrics_summary": metrics_summary,
        "metrics": metrics,
        "explanations": explanations,
        "recommendations": recommendations,
        "research_grounding": research_grounding,
        "looker_studio_ready": True,
    }


# ─────────────────────────────────────────────
# Groq Response Parsing
# ─────────────────────────────────────────────
def struct_parse_report_response(raw_response: str) -> dict:
    """
    Parse Groq's narrative JSON response.
    Expects: summary, column_explanations, explanations,
    recommendations, research_grounding.
    """
    cleaned = re.sub(r"```(?:json)?", "", raw_response).strip().strip("`").strip()

    try:
        report = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        struct_logger.error("Groq report JSON parse failed: %s\nRaw: %s", exc, raw_response[:500])
        raise ValueError(f"Failed to parse Groq report response: {exc}") from exc

    return report


# ─────────────────────────────────────────────
# Primary Reporting Entrypoint
# ─────────────────────────────────────────────
def struct_generate_report(
    audit_result: dict,
    column_classification: dict,
) -> dict:
    """
    Primary entrypoint for generating the explainability report.

    Architecture:
    - Deterministic data (metrics, metrics_summary, dataset_overview)
      is ALWAYS built in Python from audit_result
    - Groq generates ALL narrative text: summary, column_explanations (detailed),
      explanations, recommendations, research_grounding
    - If Groq fails, minimal fallback text is used
    - Response schema is guaranteed correct regardless of LLM behavior
    - Metrics are aggregated: metrics_summary per column pair,
      detailed metrics limited to top 5 worst per column pair
    """
    struct_logger.info("Generating fairness report for table '%s'.", audit_result.get("table"))

    # Try to get narrative text from Groq
    narrative = {}
    try:
        metrics_json = struct_serialize_metrics_for_prompt(audit_result, column_classification)
        prompt = struct_build_report_prompt(metrics_json)

        client = struct_get_groq_client()
        struct_logger.info("Sending audit results to Groq for narrative report generation...")
        response = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a bias detection expert. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=GROQ_TEMPERATURE
        )
        raw_text = response.choices[0].message.content
        struct_logger.debug("Groq report response (first 500 chars): %s", raw_text[:500])

        narrative = struct_parse_report_response(raw_text)
        struct_logger.info("Groq narrative generation successful.")
    except Exception as exc:
        struct_logger.error("Groq narrative generation failed: %s. Using fallback text.", exc)
        narrative = {}

    # Build the final report (deterministic structure + narrative text)
    report = struct_build_deterministic_report(audit_result, column_classification, narrative)

    struct_logger.info(
        "Report generated. bias_detected=%s, risk_level=%s, metrics=%d, recommendations=%d.",
        report.get("bias_detected"),
        report.get("risk_level"),
        len(report.get("metrics", {})),
        len(report.get("recommendations", [])),
    )
    return report


# ─────────────────────────────────────────────
# Output Serialization
# ─────────────────────────────────────────────
def struct_report_to_json(report: dict, indent: int = 2) -> str:
    """
    Serialize the report to a clean JSON string (Looker Studio-compatible).
    """
    return json.dumps(report, indent=indent, ensure_ascii=False, default=str)


def struct_save_report(report: dict, output_path: str) -> None:
    """
    Save the report JSON to a file.
    """
    json_str = struct_report_to_json(report)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(json_str)
    struct_logger.info("Report saved to: %s", output_path)