"""
struct_statistics.py
Module 3: Local Statistical Auditing
Computes fairness metrics on the FULL dataset using SQL queries on SQLite.
Metrics computed:
  - Disparate Impact Ratio (DIR)
  - Statistical Parity Difference (SPD)
  - Group-level outcome rates
  - Null/missing rate per sensitive column

Future Migration Note:
  All SQL queries use ANSI-compatible syntax and can run on BigQuery
  with table reference substitution only.
"""

import logging
import sqlite3
from typing import Optional

import pandas as pd

from app.services.struct_ingestion import struct_get_db_connection
from app.services.struct_intelligence import (
    struct_extract_columns_by_type,
    struct_get_sensitive_and_proxy_columns,
)

struct_logger = logging.getLogger("struct_statistics")

# ─────────────────────────────────────────────
# Fairness Thresholds (configurable)
# ─────────────────────────────────────────────
STRUCT_DIR_THRESHOLD = 0.8     # 4/5ths rule (EEOC guideline)
STRUCT_SPD_THRESHOLD = 0.1     # ±10% parity difference
STRUCT_MIN_GROUP_SIZE = 10     # Minimum rows per group for reliable metrics


# ─────────────────────────────────────────────
# Utility: Fetch full table as DataFrame
# ─────────────────────────────────────────────
def struct_fetch_full_table(
    table_name: str,
    conn: Optional[sqlite3.Connection] = None,
) -> pd.DataFrame:
    """
    Fetch all rows from a SQLite table.

    Args:
        table_name: Table to fetch.
        conn: Optional shared connection.

    Returns:
        pandas DataFrame of the full table.

    Future Migration:
        SELECT * FROM `project.dataset.table`
    """
    query = f"SELECT * FROM '{table_name}';"
    _conn = conn or struct_get_db_connection()
    close_after = conn is None
    try:
        df = pd.read_sql_query(query, _conn)
        struct_logger.info("Fetched full table '%s': %d rows.", table_name, len(df))
        return df
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch table '{table_name}': {exc}") from exc
    finally:
        if close_after:
            _conn.close()


# ─────────────────────────────────────────────
# Utility: Infer binary target column
# ─────────────────────────────────────────────
def struct_infer_positive_outcome(df: pd.DataFrame, target_col: str) -> object:
    """
    Infer the 'positive' outcome value for the target column.
    For binary columns: the minority class is treated as positive (e.g., 'Approved').
    Attempts common positive labels; falls back to the most frequent unique value.

    Args:
        df: Full DataFrame.
        target_col: Name of the target column.

    Returns:
        The value considered the positive outcome.
    """
    COMMON_POSITIVE = {
        1, "1", "yes", "true", "approved", "hired", "granted", "positive",
        "accept", "accepted", "qualified", "pass", "passed"
    }

    unique_vals = df[target_col].dropna().unique()

    for val in unique_vals:
        if str(val).lower() in COMMON_POSITIVE:
            struct_logger.info("Positive outcome for '%s': '%s'", target_col, val)
            return val

    # Fallback: use value_counts to pick minority class
    vc = df[target_col].value_counts()
    if len(vc) >= 2:
        positive_val = vc.index[-1]  # minority class
    else:
        positive_val = vc.index[0]

    struct_logger.info(
        "Inferred positive outcome for '%s' as minority class: '%s'.", target_col, positive_val
    )
    return positive_val


# ─────────────────────────────────────────────
# Core Fairness Metrics
# ─────────────────────────────────────────────
def struct_compute_group_rates(
    df: pd.DataFrame,
    sensitive_col: str,
    target_col: str,
    positive_outcome,
) -> dict:
    """
    Compute outcome rates per group for a sensitive column.

    Args:
        df: Full DataFrame.
        sensitive_col: The sensitive/proxy column to group by.
        target_col: The target/outcome column.
        positive_outcome: The positive outcome value.

    Returns:
        Dict mapping group_value → {count, positive_count, rate}.
    """
    group_rates = {}

    col_data = df[[sensitive_col, target_col]].copy()
    col_data[sensitive_col] = col_data[sensitive_col].astype(str).str.strip()
    col_data["_is_positive"] = col_data[target_col].astype(str).str.strip() == str(positive_outcome)

    for group_val, group_df in col_data.groupby(sensitive_col):
        count = len(group_df)
        positive_count = int(group_df["_is_positive"].sum())
        rate = round(positive_count / count, 6) if count > 0 else 0.0

        if count < STRUCT_MIN_GROUP_SIZE:
            struct_logger.warning(
                "Group '%s'='%s' has only %d rows (< min %d). Metrics may be unreliable.",
                sensitive_col, group_val, count, STRUCT_MIN_GROUP_SIZE,
            )

        group_rates[str(group_val)] = {
            "count": count,
            "positive_count": positive_count,
            "rate": rate,
            "reliable": count >= STRUCT_MIN_GROUP_SIZE,
        }

    return group_rates


def struct_compute_disparate_impact(group_rates: dict) -> dict:
    """
    Compute Disparate Impact Ratio (DIR) for all group pairs.
    DIR = P(outcome=positive | unprivileged) / P(outcome=positive | privileged)

    Privileged group = group with the highest positive outcome rate.
    All other groups are compared against the privileged group.

    Args:
        group_rates: Output of struct_compute_group_rates.

    Returns:
        Dict: {
            "privileged_group": str,
            "privileged_rate": float,
            "pairs": {group_name: {"dir": float, "flagged": bool}}
        }
    """
    if not group_rates:
        return {}

    # Identify privileged group (highest outcome rate)
    privileged = max(group_rates, key=lambda g: group_rates[g]["rate"])
    privileged_rate = group_rates[privileged]["rate"]

    pairs = {}
    for group, stats in group_rates.items():
        if group == privileged:
            continue

        unprivileged_rate = stats["rate"]

        if privileged_rate == 0:
            dir_value = None
            struct_logger.warning(
                "Privileged group '%s' has 0%% positive rate. DIR undefined.", privileged
            )
        else:
            dir_value = round(unprivileged_rate / privileged_rate, 6)

        pairs[group] = {
            "dir": dir_value,
            "flagged": (dir_value is not None and dir_value < STRUCT_DIR_THRESHOLD),
            "unprivileged_rate": unprivileged_rate,
        }

    return {
        "privileged_group": privileged,
        "privileged_rate": privileged_rate,
        "pairs": pairs,
    }


def struct_compute_statistical_parity(group_rates: dict) -> dict:
    """
    Compute Statistical Parity Difference (SPD) for all group pairs.
    SPD = P(outcome=positive | unprivileged) - P(outcome=positive | privileged)

    Args:
        group_rates: Output of struct_compute_group_rates.

    Returns:
        Dict: {
            "privileged_group": str,
            "pairs": {group_name: {"spd": float, "flagged": bool}}
        }
    """
    if not group_rates:
        return {}

    privileged = max(group_rates, key=lambda g: group_rates[g]["rate"])
    privileged_rate = group_rates[privileged]["rate"]

    pairs = {}
    for group, stats in group_rates.items():
        if group == privileged:
            continue

        spd = round(stats["rate"] - privileged_rate, 6)
        pairs[group] = {
            "spd": spd,
            "flagged": abs(spd) > STRUCT_SPD_THRESHOLD,
            "unprivileged_rate": stats["rate"],
        }

    return {
        "privileged_group": privileged,
        "privileged_rate": privileged_rate,
        "pairs": pairs,
    }


# ─────────────────────────────────────────────
# Missing Rate Analysis
# ─────────────────────────────────────────────
def struct_compute_missing_rates(df: pd.DataFrame, columns: list[str]) -> dict:
    """
    Compute null/missing value rate for each specified column.

    Args:
        df: Full DataFrame.
        columns: Columns to analyze.

    Returns:
        Dict: {column: {"null_count": int, "null_rate": float}}
    """
    result = {}
    total = len(df)
    for col in columns:
        if col not in df.columns:
            struct_logger.warning("Column '%s' not found in DataFrame; skipping.", col)
            continue
        null_count = int(df[col].isna().sum())
        result[col] = {
            "null_count": null_count,
            "null_rate": round(null_count / total, 6) if total > 0 else 0.0,
        }
    return result


# ─────────────────────────────────────────────
# Full Audit Computation
# ─────────────────────────────────────────────
def struct_run_fairness_audit(
    table_name: str,
    column_classification: dict,
    conn: Optional[sqlite3.Connection] = None,
) -> dict:
    """
    Primary entrypoint for fairness metric computation.
    Runs on the FULL dataset (not sampled).

    For each sensitive/proxy column × each target column:
      - Compute group-level outcome rates
      - Compute Disparate Impact Ratio (DIR)
      - Compute Statistical Parity Difference (SPD)

    Args:
        table_name: SQLite table containing the full dataset.
        column_classification: Output of struct_classify_columns (Module 2).
        conn: Optional shared SQLite connection.

    Returns:
        Dict with full audit results in Looker Studio–ready JSON format:
        {
            "table": str,
            "total_rows": int,
            "target_columns": [...],
            "sensitive_columns": [...],
            "proxy_columns": [...],
            "missing_rates": {...},
            "fairness_metrics": {
                target_col: {
                    sensitive_col: {
                        "group_rates": {...},
                        "disparate_impact": {...},
                        "statistical_parity": {...}
                    }
                }
            },
            "bias_detected": bool,
            "flagged_pairs": [...]
        }

    Raises:
        RuntimeError: On database or computation failure.
    """
    struct_logger.info("Starting full fairness audit on table '%s'.", table_name)

    # Fetch full dataset
    df = struct_fetch_full_table(table_name, conn=conn)
    total_rows = len(df)

    if total_rows == 0:
        raise ValueError(f"Table '{table_name}' is empty. Cannot compute fairness metrics.")

    # Extract column groups
    target_columns = struct_extract_columns_by_type(column_classification, "Target")
    sensitive_columns = struct_extract_columns_by_type(column_classification, "Sensitive")
    proxy_columns = struct_extract_columns_by_type(column_classification, "Proxy")
    bias_risk_columns = sensitive_columns + proxy_columns

    struct_logger.info(
        "Audit scope — Targets: %d, Sensitive: %d, Proxy: %d",
        len(target_columns), len(sensitive_columns), len(proxy_columns),
    )

    if not target_columns:
        struct_logger.warning("No Target columns identified. Audit will compute group statistics only.")

    if not bias_risk_columns:
        struct_logger.warning("No Sensitive or Proxy columns identified. Bias metrics may be empty.")

    # Missing rate analysis
    all_bias_cols = list(set(bias_risk_columns + target_columns))
    missing_rates = struct_compute_missing_rates(df, all_bias_cols)

    # Fairness metrics computation
    fairness_metrics: dict = {}
    flagged_pairs: list[dict] = []
    bias_detected = False

    for target_col in target_columns:
        if target_col not in df.columns:
            struct_logger.warning("Target column '%s' not in DataFrame; skipping.", target_col)
            continue

        positive_outcome = struct_infer_positive_outcome(df, target_col)
        fairness_metrics[target_col] = {}

        for sensitive_col in bias_risk_columns:
            if sensitive_col not in df.columns:
                struct_logger.warning(
                    "Sensitive/Proxy column '%s' not in DataFrame; skipping.", sensitive_col
                )
                continue

            col_type = column_classification.get(sensitive_col, {}).get("type", "Unknown")

            struct_logger.info(
                "Computing metrics: target='%s', sensitive='%s' (%s).",
                target_col, sensitive_col, col_type,
            )

            # Group rates
            group_rates = struct_compute_group_rates(df, sensitive_col, target_col, positive_outcome)

            if len(group_rates) < 2:
                struct_logger.warning(
                    "Column '%s' has fewer than 2 groups; skipping DIR/SPD.", sensitive_col
                )
                fairness_metrics[target_col][sensitive_col] = {
                    "column_type": col_type,
                    "positive_outcome": str(positive_outcome),
                    "group_rates": group_rates,
                    "disparate_impact": {},
                    "statistical_parity": {},
                    "skip_reason": "Fewer than 2 groups; metrics not meaningful.",
                }
                continue

            # Disparate Impact
            dir_result = struct_compute_disparate_impact(group_rates)

            # Statistical Parity
            spd_result = struct_compute_statistical_parity(group_rates)

            # Check for flagged pairs
            for group, dir_info in dir_result.get("pairs", {}).items():
                if dir_info.get("flagged"):
                    bias_detected = True
                    flagged_pairs.append({
                        "target_column": target_col,
                        "sensitive_column": sensitive_col,
                        "column_type": col_type,
                        "unprivileged_group": group,
                        "privileged_group": dir_result.get("privileged_group"),
                        "disparate_impact_ratio": dir_info.get("dir"),
                        "statistical_parity_difference": spd_result.get("pairs", {}).get(group, {}).get("spd"),
                        "threshold_violated": f"DIR < {STRUCT_DIR_THRESHOLD}",
                    })

            for group, spd_info in spd_result.get("pairs", {}).items():
                if spd_info.get("flagged"):
                    bias_detected = True
                    # Avoid duplicate if already flagged via DIR
                    if not any(
                        p["sensitive_column"] == sensitive_col
                        and p["unprivileged_group"] == group
                        and "statistical_parity_difference" in p
                        for p in flagged_pairs
                    ):
                        flagged_pairs.append({
                            "target_column": target_col,
                            "sensitive_column": sensitive_col,
                            "column_type": col_type,
                            "unprivileged_group": group,
                            "privileged_group": spd_result.get("privileged_group"),
                            "disparate_impact_ratio": dir_result.get("pairs", {}).get(group, {}).get("dir"),
                            "statistical_parity_difference": spd_info.get("spd"),
                            "threshold_violated": f"|SPD| > {STRUCT_SPD_THRESHOLD}",
                        })

            fairness_metrics[target_col][sensitive_col] = {
                "column_type": col_type,
                "positive_outcome": str(positive_outcome),
                "group_rates": group_rates,
                "disparate_impact": dir_result,
                "statistical_parity": spd_result,
            }

    result = {
        "table": table_name,
        "total_rows": total_rows,
        "target_columns": target_columns,
        "sensitive_columns": sensitive_columns,
        "proxy_columns": proxy_columns,
        "positive_outcome_inferred": {
            tc: str(struct_infer_positive_outcome(df, tc))
            for tc in target_columns
            if tc in df.columns
        },
        "missing_rates": missing_rates,
        "fairness_metrics": fairness_metrics,
        "bias_detected": bias_detected,
        "flagged_pairs": flagged_pairs,
        "thresholds_used": {
            "disparate_impact_ratio_min": STRUCT_DIR_THRESHOLD,
            "statistical_parity_difference_max": STRUCT_SPD_THRESHOLD,
            "min_group_size_for_reliability": STRUCT_MIN_GROUP_SIZE,
        },
    }

    struct_logger.info(
        "Fairness audit complete. bias_detected=%s, flagged_pairs=%d.",
        bias_detected, len(flagged_pairs),
    )
    return result


# ─────────────────────────────────────────────
# Summary Helper
# ─────────────────────────────────────────────
def struct_audit_summary(audit_result: dict) -> str:
    """
    Generate a concise plain-text summary of the audit result.

    Args:
        audit_result: Output of struct_run_fairness_audit.

    Returns:
        Summary string.
    """
    lines = [
        f"Table: {audit_result.get('table')}",
        f"Total Rows: {audit_result.get('total_rows')}",
        f"Bias Detected: {audit_result.get('bias_detected')}",
        f"Flagged Pairs: {len(audit_result.get('flagged_pairs', []))}",
        "",
        "Flagged Details:",
    ]
    for pair in audit_result.get("flagged_pairs", []):
        lines.append(
            f"  [{pair.get('column_type')}] {pair.get('sensitive_column')} → "
            f"{pair.get('target_column')} | Group '{pair.get('unprivileged_group')}' vs "
            f"'{pair.get('privileged_group')}' | "
            f"DIR={pair.get('disparate_impact_ratio')} | "
            f"SPD={pair.get('statistical_parity_difference')} | "
            f"Violation: {pair.get('threshold_violated')}"
        )
    return "\n".join(lines)