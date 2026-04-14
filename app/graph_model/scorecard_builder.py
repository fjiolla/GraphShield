"""
Scorecard builder module.
"""

from datetime import datetime
import pandas as pd
from app.graph_model.constants import SCORE_FAIL_BELOW, SCORE_WARN_BELOW

def compute_overall_score(universal_metrics: dict, structural_metrics: dict) -> int:
    """
    Weighted average of all metric scores.
    Universal metrics weight: 60%
    Structural metrics weight: 40%
    Return integer 0-100.
    """
    u_scores = []
    for k, v in universal_metrics.items():
        if isinstance(v, dict) and "score" in v and v["score"] is not None:
            u_scores.append(v["score"])
            
    s_scores = []
    for k, v in structural_metrics.items():
        if isinstance(v, dict) and "score" in v and v["score"] is not None:
            s_scores.append(v["score"])
            
    u_avg = sum(u_scores) / len(u_scores) if u_scores else 100
    s_avg = sum(s_scores) / len(s_scores) if s_scores else 100
    
    return int((u_avg * 0.6) + (s_avg * 0.4))

def determine_overall_status(overall_score: int) -> str:
    """
    Map score to status using thresholds from constants.py
    """
    if overall_score < SCORE_FAIL_BELOW: return "FAIL"
    if overall_score < SCORE_WARN_BELOW: return "WARN"
    return "PASS"

def extract_key_findings(universal_metrics: dict, structural_metrics: dict, groups_found: list) -> list:
    """
    Generate 3-5 plain English finding strings using actual computed values.
    Every sentence references real numbers — nothing is templated.
    """
    findings = []
    per_group = universal_metrics.get("per_group_metrics", {})

    # --- Demographic Parity finding with actual rates ---
    dp_data = universal_metrics.get("demographic_parity", {})
    if dp_data.get("status") == "FAIL" and per_group:
        rates = {g: m.get("positive_rate", 0) for g, m in per_group.items()}
        best_group = max(rates, key=rates.get)
        worst_group = min(rates, key=rates.get)
        ratio = round(rates[best_group] / rates[worst_group], 2) if rates[worst_group] > 0 else float('inf')
        findings.append(
            f"Demographic Parity FAIL (score {dp_data.get('score')}): "
            f"'{best_group}' receives positive outcomes at rate {rates[best_group]:.2%} "
            f"vs '{worst_group}' at {rates[worst_group]:.2%} ({ratio}x disparity)."
        )

    # --- Equalized Odds finding with actual value ---
    eod_data = universal_metrics.get("equalized_odds", {})
    if eod_data.get("status") == "FAIL" and eod_data.get("raw_value") is not None:
        findings.append(
            f"Equalized Odds FAIL (score {eod_data.get('score')}): "
            f"Difference of {eod_data['raw_value']:.4f} detected across groups, "
            f"exceeding the 0.1 threshold."
        )

    # --- Predictive Parity finding ---
    pp_data = universal_metrics.get("predictive_parity", {})
    if pp_data.get("status") == "FAIL" and pp_data.get("raw_value") is not None:
        findings.append(
            f"Predictive Parity FAIL (score {pp_data.get('score')}): "
            f"PPV ratio of {pp_data['raw_value']:.4f} across groups — "
            f"model is less precise for disadvantaged groups."
        )

    # --- Degree Disparity with actual per-group means ---
    deg_data = structural_metrics.get("degree_disparity", {})
    if deg_data.get("status") == "FAIL":
        pg = deg_data.get("per_group", {})
        if pg:
            best_g = max(pg, key=pg.get)
            worst_g = min(pg, key=pg.get)
            findings.append(
                f"Degree Disparity FAIL (ratio {deg_data.get('raw_value', 0):.2f}x): "
                f"'{best_g}' avg degree {pg[best_g]:.2f} vs "
                f"'{worst_g}' avg degree {pg[worst_g]:.2f} — "
                f"under-connected group has fewer opportunities."
            )

    # --- Homophily finding with actual coefficient ---
    homo_data = structural_metrics.get("homophily_coefficient", {})
    if homo_data.get("status") == "FAIL" and homo_data.get("raw_value") is not None:
        findings.append(
            f"Homophily FAIL (coefficient {homo_data['raw_value']:.4f}): "
            f"Graph is highly segregated — groups are locked into "
            f"isolated echo chambers with limited cross-group connections."
        )

    # --- Fallback if everything passes ---
    if not findings:
        findings.append("No critical fairness violations detected across all computed metrics.")

    return findings

def identify_top_risk_groups(node_df: pd.DataFrame, universal_metrics: dict) -> list:
    """Identify which groups are most disadvantaged."""
    per_group = universal_metrics.get("per_group_metrics", {})
    if not per_group: return []
    # Identify group with lowest pos rate
    rates = {g: m.get("positive_rate", 0) for g, m in per_group.items()}
    if not rates: return []
    lowest_group = min(rates, key=rates.get)
    return [lowest_group]

def build_scorecard(
    graph_metadata: dict,
    universal_metrics: dict,
    structural_metrics: dict,
    global_explanation: dict,
    protected_attr: str,
    groups_found: list,
    format_type: str,
    node_df: pd.DataFrame
) -> dict:
    """Build the complete unified scorecard."""
    overall_score = compute_overall_score(universal_metrics, structural_metrics)
    
    return {
        # "pipeline": f"graph_bias_audit_{format_type}_{protected_attr}",
        # "format": format_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "graph_metadata": {
            "node_count": graph_metadata.get("node_count"),
            "edge_count": graph_metadata.get("edge_count"),
            "is_directed": graph_metadata.get("is_directed")
        },
        "protected_attribute": protected_attr,
        "groups_found": list(groups_found),
        "universal_metrics": universal_metrics,
        "structural_metrics": structural_metrics,
        "global_explanation": global_explanation,
        "overall_score": overall_score,
        "overall_status": determine_overall_status(overall_score),
        "key_findings": extract_key_findings(universal_metrics, structural_metrics, groups_found),
        "top_risk_groups": identify_top_risk_groups(node_df, universal_metrics)
    }

if __name__ == "__main__":
    print(compute_overall_score({"a":{"score":50}}, {"b":{"score":100}}))
