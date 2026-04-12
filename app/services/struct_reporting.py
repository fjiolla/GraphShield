import json
import logging
import re
import textwrap
from typing import Optional

from app.services.struct_statistics import struct_audit_summary
from app.core.struct_local_config import struct_get_groq_client, GROQ_MODEL_NAME, GROQ_TEMPERATURE

struct_logger = logging.getLogger("struct_reporting")

STRUCT_REPORT_SCHEMA = {
    "summary": "str — Executive summary of findings",
    "bias_detected": "bool — Whether any fairness violations were found",
    "risk_level": "str — 'High' | 'Medium' | 'Low' | 'None'",
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
            "reason": "str",
            "bias_risk_explanation": "str",
        }
    },
    "metrics": {
        "<target_col>.<sensitive_col>": {
            "disparate_impact_ratio": "float | null",
            "statistical_parity_difference": "float | null",
            "privileged_group": "str",
            "unprivileged_group": "str",
            "flagged": "bool",
        }
    },
    "explanations": {
        "disparate_impact": "str — Plain-language explanation of DIR findings",
        "statistical_parity": "str — Plain-language explanation of SPD findings",
        "proxy_risk": "str — Why proxy columns are dangerous",
    },
    "recommendations": ["list of actionable fairness improvement steps"],
    "research_grounding": {
        "reference": "str — Citation of Mehrabi et al. or other relevant work",
        "applicability": "str — How the reference applies to these findings",
    },
    "looker_studio_ready": True,
}



def struct_serialize_metrics_for_prompt(
    audit_result: dict,
    column_classification: dict,
) -> str:
    """
    Convert audit result into a compact, prompt-safe string for Gemini.
    Summarizes key metrics without overwhelming the context window.

    Args:
        audit_result: Output of struct_run_fairness_audit (Module 3).
        column_classification: Output of struct_classify_columns (Module 2).

    Returns:
        JSON string of distilled metrics.
    """
    distilled = {
        "table": audit_result.get("table"),
        "total_rows": audit_result.get("total_rows"),
        "bias_detected": audit_result.get("bias_detected"),
        "target_columns": audit_result.get("target_columns"),
        "sensitive_columns": audit_result.get("sensitive_columns"),
        "proxy_columns": audit_result.get("proxy_columns"),
        "thresholds": audit_result.get("thresholds_used"),
        "flagged_pairs": audit_result.get("flagged_pairs", []),
        "missing_rates": audit_result.get("missing_rates", {}),
        "column_classification": {
            col: {"type": meta.get("type"), "reason": meta.get("reason")}
            for col, meta in column_classification.items()
        },
    }

    # Include per-group rates for flagged columns only (to keep prompt concise)
    flagged_sensitive_cols = set(
        p["sensitive_column"] for p in audit_result.get("flagged_pairs", [])
    )
    flagged_target_cols = set(
        p["target_column"] for p in audit_result.get("flagged_pairs", [])
    )

    group_rates_summary = {}
    for target_col in flagged_target_cols:
        group_rates_summary[target_col] = {}
        for sensitive_col in flagged_sensitive_cols:
            metrics = (
                audit_result.get("fairness_metrics", {})
                .get(target_col, {})
                .get(sensitive_col, {})
            )
            if metrics:
                group_rates_summary[target_col][sensitive_col] = metrics.get("group_rates", {})

    distilled["group_rates_for_flagged"] = group_rates_summary

    return json.dumps(distilled, indent=2, default=str)


# ─────────────────────────────────────────────
# Gemini Report Prompt
# ─────────────────────────────────────────────
def struct_build_report_prompt(metrics_json: str) -> str:
    """
    Build the Gemini prompt for generating the explainability report.

    Args:
        metrics_json: Compact JSON string of audit metrics.

    Returns:
        Prompt string.
    """
    prompt = textwrap.dedent(f"""
    You are a senior AI fairness researcher and explainability expert.
    Your role is to analyze bias detection results and generate a clear,
    actionable fairness report that both technical and non-technical stakeholders can understand.

    AUDIT RESULTS:
    {metrics_json}

    FAIRNESS DEFINITIONS (use these exact definitions in your explanations):
    - Disparate Impact Ratio (DIR): P(positive outcome | unprivileged group) / P(positive outcome | privileged group).
      Flagged if DIR < 0.8 (EEOC 4/5ths rule).
    - Statistical Parity Difference (SPD): P(positive outcome | unprivileged) - P(positive outcome | privileged).
      Flagged if |SPD| > 0.1.
    - Proxy Bias: A feature (e.g., Zip_Code) that is not a sensitive attribute itself,
      but correlates with one, thereby introducing indirect discrimination.

    RESEARCH GROUNDING:
    Reference: Mehrabi, N., Morstatter, F., Saxena, N., Lerman, K., & Galstyan, A. (2021).
    "A Survey on Bias and Fairness in Machine Learning." ACM Computing Surveys, 54(6), 1–35.
    Use this and relevant fairness research to ground your recommendations.

    TASK: Generate a comprehensive fairness report as STRICT JSON.

    CRITICAL INSTRUCTIONS:
    1. Return ONLY valid JSON. No markdown, no code fences, no preamble.
    2. All string values must be plain text (no HTML or markdown inside JSON strings).
    3. "recommendations" must be a list of at least 3 concrete, actionable items.
    4. "risk_level" must be one of: "High", "Medium", "Low", "None".
    5. "metrics" must include one entry per flagged pair using key format "target_col.sensitive_col.group".
    6. Ground recommendations in fairness research (Mehrabi et al. or equivalent).
    7. Explain proxy bias risk clearly for any Proxy columns found.

    OUTPUT FORMAT (STRICT):
    {{
      "summary": "2-3 sentence executive summary of bias findings.",
      "bias_detected": true,
      "risk_level": "High | Medium | Low | None",
      "dataset_overview": {{
        "table_name": "...",
        "total_rows": 0,
        "target_columns": [],
        "sensitive_columns": [],
        "proxy_columns": []
      }},
      "column_explanations": {{
        "<column_name>": {{
          "type": "Sensitive | Proxy | Target | Safe",
          "reason": "Why this column was classified this way.",
          "bias_risk_explanation": "Specific risk this column poses to model fairness."
        }}
      }},
      "metrics": {{
        "<target_col>.<sensitive_col>.<group>": {{
          "disparate_impact_ratio": 0.0,
          "statistical_parity_difference": 0.0,
          "privileged_group": "...",
          "unprivileged_group": "...",
          "flagged": true,
          "interpretation": "Plain-language meaning of these numbers."
        }}
      }},
      "explanations": {{
        "disparate_impact": "What DIR findings mean for this dataset.",
        "statistical_parity": "What SPD findings mean for this dataset.",
        "proxy_risk": "How proxy columns could introduce hidden discrimination."
      }},
      "recommendations": [
        "Specific action 1 with justification.",
        "Specific action 2 with justification.",
        "Specific action 3 with justification."
      ],
      "research_grounding": {{
        "reference": "Full citation of Mehrabi et al. (2021) or other relevant work.",
        "applicability": "How this research applies to the specific findings in this audit."
      }},
      "looker_studio_ready": true
    }}
    """).strip()

    return prompt


# ─────────────────────────────────────────────
# Gemini Response Parsing
# ─────────────────────────────────────────────
def struct_parse_report_response(raw_response: str) -> dict:
    """
    Parse and validate Gemini's report JSON response.
    Strips markdown fences, validates required fields.

    Args:
        raw_response: Raw text from Gemini.

    Returns:
        Parsed report dict.

    Raises:
        ValueError: If parsing fails and fallback is used.
    """
    cleaned = re.sub(r"```(?:json)?", "", raw_response).strip().strip("`").strip()

    try:
        report = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        struct_logger.error("Gemini report JSON parse failed: %s\nRaw: %s", exc, raw_response[:500])
        raise ValueError(f"Failed to parse Gemini report response: {exc}") from exc

    # Validate required top-level keys
    required_keys = [
        "summary", "bias_detected", "risk_level", "dataset_overview",
        "column_explanations", "metrics", "explanations",
        "recommendations", "research_grounding",
    ]

    missing_keys = [k for k in required_keys if k not in report]
    if missing_keys:
        struct_logger.warning("Report missing keys: %s. Inserting placeholders.", missing_keys)
        for key in missing_keys:
            if key == "recommendations":
                report[key] = ["Manual review of flagged columns is recommended."]
            elif key == "bias_detected":
                report[key] = False
            elif key == "risk_level":
                report[key] = "Unknown"
            elif key in ("metrics", "explanations", "column_explanations",
                         "dataset_overview", "research_grounding"):
                report[key] = {}
            else:
                report[key] = "Not available."

    report["looker_studio_ready"] = True
    return report


# ─────────────────────────────────────────────
# Fallback Report (when Gemini is unavailable)
# ─────────────────────────────────────────────
def struct_build_fallback_report(
    audit_result: dict,
    column_classification: dict,
) -> dict:
    """
    Build a structured fallback report using only statistical results
    when Gemini is unavailable.

    Args:
        audit_result: Output of struct_run_fairness_audit.
        column_classification: Output of struct_classify_columns.

    Returns:
        Fallback report dict in the standard schema.
    """
    bias_detected = audit_result.get("bias_detected", False)
    flagged_pairs = audit_result.get("flagged_pairs", [])

    risk_level = "None"
    if flagged_pairs:
        risk_level = "High" if len(flagged_pairs) > 3 else "Medium"

    summary = (
        f"Automated audit of table '{audit_result.get('table')}' "
        f"({audit_result.get('total_rows')} rows) found "
        f"{'bias violations' if bias_detected else 'no significant bias violations'}. "
        f"{len(flagged_pairs)} group pairs were flagged."
    )

    metrics = {}
    for pair in flagged_pairs:
        key = f"{pair['target_column']}.{pair['sensitive_column']}.{pair['unprivileged_group']}"
        metrics[key] = {
            "disparate_impact_ratio": pair.get("disparate_impact_ratio"),
            "statistical_parity_difference": pair.get("statistical_parity_difference"),
            "privileged_group": pair.get("privileged_group"),
            "unprivileged_group": pair.get("unprivileged_group"),
            "flagged": True,
            "interpretation": f"This group violated the threshold: {pair.get('threshold_violated')}.",
        }

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
        "column_explanations": {
            col: {
                "type": meta.get("type"),
                "reason": meta.get("reason"),
                "bias_risk_explanation": (
                    "This column was flagged as a risk factor." 
                    if meta.get("type") in ("Sensitive", "Proxy") 
                    else "Low bias risk."
                ),
            }
            for col, meta in column_classification.items()
        },
        "metrics": metrics,
        "explanations": {
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
        },
        "recommendations": [
            "Remove or encode Sensitive and Proxy columns before training production models.",
            "Apply fairness-aware training techniques (reweighting, adversarial debiasing).",
            "Monitor model outputs by demographic group in production (ongoing fairness audit).",
            "Consult Mehrabi et al. (2021) for a comprehensive bias mitigation framework.",
        ],
        "research_grounding": {
            "reference": (
                "Mehrabi, N., Morstatter, F., Saxena, N., Lerman, K., & Galstyan, A. (2021). "
                "A Survey on Bias and Fairness in Machine Learning. "
                "ACM Computing Surveys, 54(6), 1–35. https://doi.org/10.1145/3457607"
            ),
            "applicability": (
                "The definitions of Disparate Impact and Statistical Parity used in this audit "
                "align with the group fairness taxonomy in Mehrabi et al. Section 3."
            ),
        },
        "looker_studio_ready": True,
        "gemini_unavailable": True,
    }


# ─────────────────────────────────────────────
# Primary Reporting Entrypoint
# ─────────────────────────────────────────────
def struct_generate_report(
    audit_result: dict,
    column_classification: dict,
) -> dict:
    """
    Primary entrypoint for generating the explainability report.

    Pipeline:
    1. Serialize audit metrics for Gemini prompt
    2. Build structured Gemini prompt
    3. Send to Gemini Pro for narrative generation
    4. Parse and validate JSON response
    5. Return Looker Studio-ready report

    Falls back to a structured statistical report if Gemini is unavailable.

    Args:
        audit_result: Output of struct_run_fairness_audit (Module 3).
        column_classification: Output of struct_classify_columns (Module 2).

    Returns:
        Looker Studio-ready report dict (STRICT JSON structure).
    """
    struct_logger.info("Generating fairness report for table '%s'.", audit_result.get("table"))

    # Serialize metrics for prompt
    metrics_json = struct_serialize_metrics_for_prompt(audit_result, column_classification)

    # Build Gemini prompt
    prompt = struct_build_report_prompt(metrics_json)

    # Call Gemini
    try:
        # model = struct_get_gemini_model()
        # struct_logger.info("Sending audit results to Gemini for narrative report generation...")
        # response = model.generate_content(prompt)
        # raw_text = response.text
        # struct_logger.debug("Gemini report response (first 500 chars): %s", raw_text[:500])
        client = struct_get_groq_client()
        struct_logger.info("Sending audit results to Groq for narrative report generation...")
        response = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{"role": "system", "content": "You are a bias detection expert. Generate a structured JSON report."},{"role": "user", "content": prompt}],
            temperature=GROQ_TEMPERATURE,
        )
        raw_text = response.choices[0].message.content
        struct_logger.debug("Groq report response (first 500 chars): %s", raw_text[:500])
    except Exception as exc:
        struct_logger.error("Gemini report generation failed: %s. Using fallback report.", exc)
        return struct_build_fallback_report(audit_result, column_classification)

    # Parse response
    try:
        report = struct_parse_report_response(raw_text)
    except ValueError:
        struct_logger.warning("Gemini response unparseable. Using fallback report.")
        return struct_build_fallback_report(audit_result, column_classification)

    # Inject raw statistical data for full traceability
    report["_raw_flagged_pairs"] = audit_result.get("flagged_pairs", [])
    report["_missing_rates"] = audit_result.get("missing_rates", {})
    report["looker_studio_ready"] = True

    struct_logger.info(
        "Report generated. bias_detected=%s, risk_level=%s, recommendations=%d.",
        report.get("bias_detected"),
        report.get("risk_level"),
        len(report.get("recommendations", [])),
    )
    return report


# ─────────────────────────────────────────────
# Output Serialization
# ─────────────────────────────────────────────
def struct_report_to_json(report: dict, indent: int = 2) -> str:
    """
    Serialize the report to a clean JSON string (Looker Studio-compatible).
    No extra formatting, markdown, or special characters.

    Args:
        report: Report dict from struct_generate_report.
        indent: JSON indentation level.

    Returns:
        JSON string.
    """
    return json.dumps(report, indent=indent, ensure_ascii=False, default=str)


def struct_save_report(report: dict, output_path: str) -> None:
    """
    Save the report JSON to a file.

    Args:
        report: Report dict.
        output_path: File path to write the report.
    """
    json_str = struct_report_to_json(report)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(json_str)
    struct_logger.info("Report saved to: %s", output_path)