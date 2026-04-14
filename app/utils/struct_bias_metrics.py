"""
struct_bias_metrics.py
Module 2 — Layer 3: Pure Fairness Metric Functions

Computes disparate impact, equalized odds, parity gap, fairness scores,
and the final bias verdict. Uses only numpy/pandas — zero ML imports.

Key metrics:
  - Disparate Impact Ratio (80% rule — Uniform Guidelines 1978)
  - Equalized Odds (TPR + FPR parity)
  - Statistical Parity Gap
  - Composite Fairness Score (0–100 scale)

Verdict logic:
  BIASED   → any DIR < 0.8 OR parity_gap > 0.2
  MARGINAL → all ratios 0.8–0.9 AND parity_gap 0.1–0.2
  FAIR     → all ratios >= 0.9 AND parity_gap < 0.1
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from app.schemas.struct_model_audit_schema import StructBiasVerdict

struct_logger = logging.getLogger("struct_bias_metrics")


# ─────────────────────────────────────────────
# Disparate Impact Ratio
# 80% rule — Uniform Guidelines on Employee Selection 1978
# ─────────────────────────────────────────────
def compute_disparate_impact(
    y_pred: list | np.ndarray,
    groups: list | np.ndarray,
) -> dict:
    """
    Compute disparate impact ratio per group.
    
    The 80% rule (4/5ths rule) states that the positive outcome rate of any
    unprivileged group must be at least 80% of the privileged group's rate.
    
    Args:
        y_pred: Binary predictions (0 or 1).
        groups: Group labels for each prediction.
    
    Returns:
        Dict with per-group positive_rate, disparate_impact_ratio, flagged status,
        and the identified privileged_group.
    """
    y_pred = np.array(y_pred, dtype=int)
    groups = np.array(groups, dtype=str)

    unique_groups = np.unique(groups)
    group_rates = {}

    for g in unique_groups:
        g = str(g)  # Convert numpy.str_ to native str
        mask = groups == g
        count = int(mask.sum())
        if count == 0:
            continue
        positive_rate = float(y_pred[mask].sum()) / count
        group_rates[g] = positive_rate

    if not group_rates:
        return {
            "privileged_group": None,
            "groups": {},
            "error": "No valid groups found",
        }

    # Privileged group = group with highest positive rate
    privileged_group = str(max(group_rates, key=group_rates.get))
    privileged_rate = float(group_rates[privileged_group])

    result = {
        "privileged_group": privileged_group,
        "privileged_rate": round(float(privileged_rate), 6),
        "groups": {},
    }

    for g, rate in group_rates.items():
        if privileged_rate > 0:
            ratio = rate / privileged_rate
        else:
            # If privileged group has 0 rate, ratio is undefined
            ratio = 1.0 if rate == 0 else float("inf")

        flagged = bool(ratio < 0.8)  # Convert numpy.bool_ to native bool
        result["groups"][str(g)] = {
            "positive_rate": round(float(rate), 6),
            "disparate_impact_ratio": round(float(ratio), 6),
            "flagged": flagged,
            "sample_count": int((np.array(groups) == g).sum()),
        }

    struct_logger.info(
        "Disparate impact computed. Privileged group: '%s' (rate=%.4f). "
        "Flagged groups: %s",
        str(privileged_group),
        float(privileged_rate),
        [g for g, d in result["groups"].items() if d["flagged"]],
    )

    return result


# ─────────────────────────────────────────────
# Equalized Odds (TPR + FPR per group)
# ─────────────────────────────────────────────
def compute_equalized_odds(
    y_pred: list | np.ndarray,
    y_true: Optional[list | np.ndarray],
    groups: list | np.ndarray,
) -> dict:
    """
    Compute True Positive Rate and False Positive Rate per group.
    
    If y_true is None, returns TPR/FPR as None with a note that
    ground truth is not available.
    
    Args:
        y_pred: Binary predictions.
        y_true: Actual labels (ground truth). Can be None.
        groups: Group labels.
    
    Returns:
        Dict with per-group TPR and FPR.
    """
    y_pred = np.array(y_pred, dtype=int)
    groups = np.array(groups, dtype=str)

    if y_true is None:
        unique_groups = np.unique(groups)
        return {
            str(g): {
                "true_positive_rate": None,
                "false_positive_rate": None,
                "note": "ground truth not available",
            }
            for g in unique_groups
        }

    y_true = np.array(y_true, dtype=int)
    unique_groups = np.unique(groups)
    result = {}

    for g_raw in unique_groups:
        g = str(g_raw)  # Ensure native str key
        mask = groups == g_raw
        g_pred = y_pred[mask]
        g_true = y_true[mask]

        # True Positive Rate = TP / (TP + FN)
        positives = g_true == 1
        if positives.sum() > 0:
            tpr = float((g_pred[positives] == 1).sum() / positives.sum())
        else:
            tpr = 0.0

        # False Positive Rate = FP / (FP + TN)
        negatives = g_true == 0
        if negatives.sum() > 0:
            fpr = float((g_pred[negatives] == 1).sum() / negatives.sum())
        else:
            fpr = 0.0

        result[g] = {
            "true_positive_rate": round(tpr, 6),
            "false_positive_rate": round(fpr, 6),
        }

    return result


# ─────────────────────────────────────────────
# Parity Gap
# ─────────────────────────────────────────────
def compute_parity_gap(
    y_pred: list | np.ndarray,
    groups: list | np.ndarray,
) -> float:
    """
    Compute the parity gap: max positive rate - min positive rate across groups.
    
    A larger parity gap indicates greater disparity in outcomes between groups.
    
    Args:
        y_pred: Binary predictions.
        groups: Group labels.
    
    Returns:
        Float representing the parity gap.
    """
    y_pred = np.array(y_pred, dtype=int)
    groups = np.array(groups, dtype=str)

    unique_groups = np.unique(groups)
    rates = []

    for g in unique_groups:
        mask = groups == g
        count = mask.sum()
        if count == 0:
            continue
        rate = y_pred[mask].sum() / count
        rates.append(rate)

    if len(rates) < 2:
        return 0.0

    gap = float(max(rates) - min(rates))
    return round(gap, 6)


# ─────────────────────────────────────────────
# Fairness Score (0–100 scale)
# ─────────────────────────────────────────────
def compute_fairness_score(
    metric_value: float,
    metric_type: str,
) -> float:
    """
    Convert a raw metric value to a 0–100 fairness score.
    
    Mapping:
      disparate_impact → min(ratio, 1.0) * 100
      parity_gap       → max(0, (1 - gap)) * 100
    
    Args:
        metric_value: Raw metric value.
        metric_type: One of 'disparate_impact' or 'parity_gap'.
    
    Returns:
        Float score rounded to 2 decimal places.
    """
    if metric_type == "disparate_impact":
        score = min(float(metric_value), 1.0) * 100
    elif metric_type == "parity_gap":
        score = max(0.0, (1.0 - float(metric_value))) * 100
    else:
        # Default: treat as ratio
        score = min(float(metric_value), 1.0) * 100

    return round(score, 2)


# ─────────────────────────────────────────────
# Bias Verdict
# ─────────────────────────────────────────────
def compute_bias_verdict(
    disparate_impact_dict: dict,
    parity_gap: float,
) -> StructBiasVerdict:
    """
    Compute the final bias verdict from disparate impact results and parity gap.
    
    Verdict logic:
      BIASED   → any DIR < 0.8 OR parity_gap > 0.2
      MARGINAL → all ratios 0.8–0.9 AND parity_gap 0.1–0.2
      FAIR     → all ratios >= 0.9 AND parity_gap < 0.1
    
    bias_confidence:
      High   → 2+ groups flagged
      Medium → exactly 1 group flagged
      Low    → 0 groups flagged but marginal values present
    
    Args:
        disparate_impact_dict: Output from compute_disparate_impact().
        parity_gap: Output from compute_parity_gap().
    
    Returns:
        StructBiasVerdict with all fields populated.
    """
    groups_data = disparate_impact_dict.get("groups", {})
    privileged_group = disparate_impact_dict.get("privileged_group", "Unknown")

    flagged_groups = []
    marginal_groups = []
    worst_group = None
    worst_dir = float("inf")

    for g, data in groups_data.items():
        ratio = data.get("disparate_impact_ratio", 1.0)

        if ratio < worst_dir:
            worst_dir = ratio
            worst_group = g

        if data.get("flagged", False):
            flagged_groups.append(g)

        # Marginal: ratio between 0.8 and 0.9
        if 0.8 <= ratio < 0.9:
            marginal_groups.append(g)

    flagged_count = len(flagged_groups)

    # ── Determine verdict ──
    any_ratio_below_08 = any(
        groups_data[g].get("disparate_impact_ratio", 1.0) < 0.8
        for g in groups_data
    )

    all_ratios_08_to_09 = all(
        0.8 <= groups_data[g].get("disparate_impact_ratio", 1.0) < 0.9
        for g in groups_data
        if g != privileged_group
    )

    all_ratios_above_09 = all(
        groups_data[g].get("disparate_impact_ratio", 1.0) >= 0.9
        for g in groups_data
    )

    if any_ratio_below_08 or parity_gap > 0.2:
        bias_verdict = "BIASED"
        is_biased = True
    elif all_ratios_08_to_09 and 0.1 <= parity_gap <= 0.2:
        bias_verdict = "MARGINAL"
        is_biased = False
    elif all_ratios_above_09 and parity_gap < 0.1:
        bias_verdict = "FAIR"
        is_biased = False
    else:
        # Edge cases: default to MARGINAL if not clearly BIASED or FAIR
        if flagged_count > 0:
            bias_verdict = "BIASED"
            is_biased = True
        elif marginal_groups:
            bias_verdict = "MARGINAL"
            is_biased = False
        else:
            bias_verdict = "FAIR"
            is_biased = False

    # ── Determine confidence ──
    if flagged_count >= 2:
        bias_confidence = "High"
    elif flagged_count == 1:
        bias_confidence = "Medium"
    elif marginal_groups:
        bias_confidence = "Low"
    else:
        bias_confidence = "Low"

    # ── Build verdict reason ──
    if worst_group and worst_group != privileged_group:
        verdict_reason = (
            f"Group '{worst_group}' has disparate impact ratio of "
            f"{round(worst_dir, 4)} vs privileged group '{privileged_group}'. "
            f"Parity gap: {round(parity_gap, 4)}. "
        )
        if worst_dir < 0.8:
            verdict_reason += "Violates 80% rule threshold."
        elif worst_dir < 0.9:
            verdict_reason += "Marginal — approaching 80% rule threshold."
        else:
            verdict_reason += "Within acceptable fairness bounds."
    else:
        verdict_reason = (
            f"All groups show similar outcome rates. "
            f"Parity gap: {round(parity_gap, 4)}. "
            f"{'No violations detected.' if bias_verdict == 'FAIR' else 'Minor disparities observed.'}"
        )

    # Handle edge case: worst_group is None
    if worst_group is None:
        worst_group = privileged_group or "Unknown"
    if worst_dir == float("inf"):
        worst_dir = 1.0

    struct_logger.info(
        "Bias verdict: %s (confidence=%s, flagged=%d, worst_group='%s', worst_DIR=%.4f, parity_gap=%.4f)",
        bias_verdict, bias_confidence, flagged_count, worst_group, worst_dir, parity_gap,
    )

    return StructBiasVerdict(
        is_model_biased=is_biased,
        bias_verdict=bias_verdict,
        bias_confidence=bias_confidence,
        verdict_reason=verdict_reason,
        flagged_metrics_count=flagged_count,
        worst_group=worst_group,
        worst_disparate_impact_ratio=round(float(worst_dir), 6),
    )


# ─────────────────────────────────────────────
# Full Metrics (convenience wrapper)
# ─────────────────────────────────────────────
def compute_full_metrics(
    y_pred: list | np.ndarray,
    y_true: Optional[list | np.ndarray],
    groups: list | np.ndarray,
) -> dict:
    """
    Compute all fairness metrics in one call.
    
    Returns a combined dict with:
      - disparate_impact: per-group DIR analysis
      - equalized_odds: per-group TPR/FPR
      - parity_gap: float
    
    Args:
        y_pred: Binary predictions.
        y_true: Actual labels (can be None).
        groups: Group labels.
    
    Returns:
        Combined metrics dict.
    """
    di = compute_disparate_impact(y_pred, groups)
    eo = compute_equalized_odds(y_pred, y_true, groups)
    pg = compute_parity_gap(y_pred, groups)

    return {
        "disparate_impact": di,
        "equalized_odds": eo,
        "parity_gap": pg,
    }
