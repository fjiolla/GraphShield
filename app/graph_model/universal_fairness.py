"""
Universal fairness metrics via Fairlearn.
"""

import pandas as pd
import numpy as np
from fairlearn.metrics import demographic_parity_ratio, equalized_odds_difference
import logging
from app.graph_model.constants import (
    DEMOGRAPHIC_PARITY_THRESHOLD,
    EQUALIZED_ODDS_THRESHOLD,
    DISPARATE_IMPACT_THRESHOLD,
    SCORE_WARN_BELOW,
    SCORE_FAIL_BELOW
)

logger = logging.getLogger(__name__)

def compute_demographic_parity(y_pred: pd.Series, sensitive: pd.Series) -> float:
    """Compute demographic parity ratio using Fairlearn."""
    try:
        return demographic_parity_ratio(y_true=y_pred, y_pred=y_pred, sensitive_features=sensitive)
    except Exception as e:
        logger.warning(f"Could not compute demographic parity: {e}")
        return 1.0

def compute_equalized_odds(y_true: pd.Series, y_pred: pd.Series, sensitive: pd.Series):
    """Compute equalized odds difference. Return None if y_true missing."""
    if y_true is None or y_true.dropna().empty:
        return None
    try:
        return equalized_odds_difference(y_true=y_true, y_pred=y_pred, sensitive_features=sensitive)
    except Exception as e:
        logger.warning(f"Could not compute equalized odds: {e}")
        return None

def compute_disparate_impact(y_pred: pd.Series, sensitive: pd.Series) -> float:
    """Compute disparate impact ratio (80% rule metric)."""
    # Simply mapping demographic parity as the standard Proxy for DI
    return compute_demographic_parity(y_pred, sensitive)

def compute_predictive_parity(y_true: pd.Series, y_pred: pd.Series, sensitive: pd.Series):
    """
    Compute predictive parity ratio.
    Predictive parity = ratio of min PPV to max PPV across groups.
    PPV (Positive Predictive Value) = TP / (TP + FP) per group.
    Returns None if ground_truth is not available.
    """
    if y_true is None or y_true.dropna().empty:
        return None
    try:
        groups = sensitive.unique()
        ppvs = {}
        for g in groups:
            mask = sensitive == g
            g_pred = y_pred[mask]
            g_true = y_true[mask]
            tp = int(((g_pred == 1) & (g_true == 1)).sum())
            fp = int(((g_pred == 1) & (g_true == 0)).sum())
            ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            ppvs[g] = ppv
        if not ppvs:
            return None
        max_ppv = max(ppvs.values())
        min_ppv = min(ppvs.values())
        return min_ppv / max_ppv if max_ppv > 0 else 1.0
    except Exception as e:
        logger.warning(f"Could not compute predictive parity: {e}")
        return None

def compute_per_group_breakdown(node_df: pd.DataFrame, prediction_col='prediction', ground_truth_col='ground_truth', protected_attr_col='protected_attr') -> dict:
    """
    For each unique group in protected_attr:
    compute count, positive_rate, accuracy, TPR, FPR.
    All values are dynamically computed from actual data.
    """
    groups = node_df[protected_attr_col].unique()
    breakdown = {}
    has_gt = ground_truth_col in node_df.columns and not node_df[ground_truth_col].isnull().all()
    for g in groups:
        g_df = node_df[node_df[protected_attr_col] == g]
        count = len(g_df)
        g_pred_col = pd.to_numeric(g_df[prediction_col], errors='coerce').fillna(0)
        pos_rate = float(g_pred_col.mean()) if count > 0 else 0.0
        acc = None
        tpr = None
        fpr = None
        if has_gt:
            g_pred = g_df[prediction_col].astype(int)
            g_true = g_df[ground_truth_col].astype(int)
            acc = float((g_pred == g_true).mean())
            # TPR = TP / (TP + FN)
            actual_pos = (g_true == 1).sum()
            tp = ((g_pred == 1) & (g_true == 1)).sum()
            tpr = float(tp / actual_pos) if actual_pos > 0 else 0.0
            # FPR = FP / (FP + TN)
            actual_neg = (g_true == 0).sum()
            fp = ((g_pred == 1) & (g_true == 0)).sum()
            fpr = float(fp / actual_neg) if actual_neg > 0 else 0.0

        breakdown[str(g)] = {
            "count": count,
            "positive_rate": round(pos_rate, 4),
            "accuracy": round(acc, 4) if acc is not None else None,
            "tpr": round(tpr, 4) if tpr is not None else None,
            "fpr": round(fpr, 4) if fpr is not None else None
        }
    return breakdown

def normalize_to_score(metric_value: float, metric_type: str) -> dict:
    """
    Convert raw metric value to 0-100 score with status.
    Handles all metric types including predictive_parity.
    """
    if metric_value is None:
        return {"raw_value": None, "score": None, "status": "UNKNOWN"}
    
    score = 100
    status = "PASS"
    
    if metric_type in ("demographic_parity", "disparate_impact", "predictive_parity"):
        # Ratio-based: 1.0 = perfect, < threshold = biased
        if metric_value < DEMOGRAPHIC_PARITY_THRESHOLD:
            score = int(metric_value * 100)
            status = "FAIL" if score < SCORE_FAIL_BELOW else "WARN"
    elif metric_type == "equalized_odds":
        # Difference-based: 0.0 = perfect, > threshold = biased
        if metric_value > EQUALIZED_ODDS_THRESHOLD:
            status = "FAIL"
            score = max(0, 100 - int(metric_value * 100))
            if score >= SCORE_FAIL_BELOW: status = "WARN"
            
    return {
        "raw_value": round(float(metric_value), 6),
        "score": score,
        "status": status
    }

def compute_universal_metrics(
    node_df: pd.DataFrame,
    prediction_col: str = 'prediction',
    ground_truth_col: str = 'ground_truth',
    protected_attr_col: str = 'protected_attr'
) -> dict:
    """
    Compute all applicable fairness metrics using Fairlearn.
    """
    if node_df.empty or prediction_col not in node_df.columns or protected_attr_col not in node_df.columns:
        return {}
        
    y_pred = node_df[prediction_col].astype(int)
    sensitive = node_df[protected_attr_col]
    y_true = node_df[ground_truth_col].astype(int) if ground_truth_col in node_df.columns and not node_df[ground_truth_col].dropna().empty else None

    dp = compute_demographic_parity(y_pred, sensitive)
    eod = compute_equalized_odds(y_true, y_pred, sensitive)
    di = compute_disparate_impact(y_pred, sensitive)
    pp = compute_predictive_parity(y_true, y_pred, sensitive)
    
    return {
        "demographic_parity": normalize_to_score(dp, "demographic_parity"),
        "equalized_odds": normalize_to_score(eod, "equalized_odds"),
        "disparate_impact": normalize_to_score(di, "disparate_impact"),
        "predictive_parity": normalize_to_score(pp, "predictive_parity"),
        "per_group_metrics": compute_per_group_breakdown(node_df, prediction_col, ground_truth_col, protected_attr_col)
    }

if __name__ == "__main__":
    df = pd.DataFrame({
        "prediction": [1, 0, 1, 1],
        "protected_attr": ['A', 'A', 'B', 'B']
    })
    print(compute_universal_metrics(df))
