import json
import logging
import re
import sqlite3
import textwrap
from typing import Optional

import pandas as pd

from app.services.struct_ingestion import struct_get_db_connection
from app.core.struct_local_config import (
    struct_get_groq_client,
    GROQ_MODEL_NAME,
    GROQ_TEMPERATURE
)

struct_logger = logging.getLogger("struct_intelligence")

# ─────────────────────────────────────────────
# Column type taxonomy
# ─────────────────────────────────────────────
STRUCT_VALID_COLUMN_TYPES = {"Target", "Sensitive", "Proxy", "Safe"}

STRUCT_TYPE_DESCRIPTIONS = {
    "Target": "The outcome variable the model predicts (e.g., Loan_Approved, Hired).",
    "Sensitive": "A protected attribute that should not influence decisions (e.g., Race, Gender, Age).",
    "Proxy": (
        "A seemingly neutral feature that correlates with a sensitive attribute "
        "and can introduce indirect bias (e.g., Zip_Code → Proxy for Race/Income)."
    ),
    "Safe": "A legitimate, non-biasing feature that is safe to use in modeling.",
}


def struct_sample_table(
    table_name: str,
    limit: int = 50,
    conn: Optional[sqlite3.Connection] = None,
) -> pd.DataFrame:
    """
    Query a random sample of rows from the SQLite table for Gemini analysis.
    Uses ORDER BY RANDOM() to avoid positional bias in sampling.

    Args:
        table_name: SQLite table to sample.
        limit: Maximum number of rows to sample.
        conn: Optional existing SQLite connection.

    Returns:
        pandas DataFrame of sampled rows.

    Raises:
        RuntimeError: If the query fails.

    Future Migration:
        Replace with BigQuery:
            SELECT * FROM `project.dataset.table` ORDER BY RAND() LIMIT {limit}
    """
    query = f"SELECT * FROM '{table_name}' ORDER BY RANDOM() LIMIT {limit};"
    _conn = conn or struct_get_db_connection()
    close_after = conn is None

    try:
        df = pd.read_sql_query(query, _conn)
        struct_logger.info(
            "Sampled %d rows from table '%s' for Gemini classification.", len(df), table_name
        )
        return df
    except Exception as exc:
        raise RuntimeError(f"Sampling failed for table '{table_name}': {exc}") from exc
    finally:
        if close_after:
            _conn.close()


# ─────────────────────────────────────────────
# Column Profile Summary
# ─────────────────────────────────────────────
def struct_build_column_profile(df: pd.DataFrame) -> dict:
    """
    Build a lightweight column profile to enrich Gemini's context.
    Includes dtype, nullability, unique value count, and sample values.

    Args:
        df: Sampled DataFrame.

    Returns:
        Dict mapping column_name → profile dict.
    """
    profile = {}
    for col in df.columns:
        series = df[col].dropna()
        unique_vals = series.nunique()
        sample_vals = series.unique()[:5].tolist()

        profile[col] = {
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isna().sum()),
            "unique_count": unique_vals,
            "sample_values": [str(v) for v in sample_vals],
            "high_cardinality": unique_vals > 50,
        }
    return profile


# ─────────────────────────────────────────────
# Gemini Prompt Construction
# ─────────────────────────────────────────────
def struct_build_classification_prompt(column_profile: dict) -> str:
    """
    Build a structured Gemini prompt for column-level bias classification.
    Instructs Gemini to return STRICT JSON only.

    Args:
        column_profile: Output of struct_build_column_profile.

    Returns:
        Prompt string ready for Gemini.
    """
    col_descriptions = json.dumps(column_profile, indent=2)

    prompt = textwrap.dedent(f"""
    You are an expert AI fairness auditor specializing in algorithmic bias detection.

    Below is a profile of columns from a dataset. For EACH column, classify it into
    EXACTLY ONE of these four types:

    - "Target": The outcome/label variable the model predicts.
    - "Sensitive": A legally/ethically protected attribute (race, gender, age, religion, etc.).
    - "Proxy": A seemingly neutral feature that INDIRECTLY encodes a sensitive attribute
      and can introduce bias. You MUST explain the proxy relationship clearly.
      Example: "Zip_Code" → Proxy for Race/Income due to residential segregation.
    - "Safe": A legitimate, non-biasing feature safe for modeling.

    COLUMN PROFILES:
    {col_descriptions}

    CRITICAL INSTRUCTIONS:
    1. Return ONLY valid JSON. No markdown, no preamble, no explanation outside JSON.
    2. For EVERY column, explain your reasoning in "reason".
    3. Proxy columns MUST clearly name the sensitive attribute they proxy.
    4. For high-cardinality columns (unique_count > 50), carefully assess proxy risk.
    5. Empty or mostly-null columns should be classified as "Safe" with a note.

    OUTPUT FORMAT (STRICT — no deviations):
    {{
      "column_name_1": {{
        "type": "Target | Sensitive | Proxy | Safe",
        "reason": "Detailed explanation of classification and any bias risk."
      }},
      "column_name_2": {{
        "type": "Target | Sensitive | Proxy | Safe",
        "reason": "..."
      }}
    }}
    """).strip()

    return prompt


# ─────────────────────────────────────────────
# Gemini Response Parsing
# ─────────────────────────────────────────────
def struct_parse_gemini_classification(
    raw_response: str,
    expected_columns: list[str],
) -> dict:
    """
    Parse and validate Gemini's JSON classification response.
    Falls back to 'Safe' classification for missing or invalid columns.

    Args:
        raw_response: Raw text response from Gemini.
        expected_columns: List of columns that should be classified.

    Returns:
        Dict: {column_name: {"type": str, "reason": str}}
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw_response).strip()
    cleaned = cleaned.strip("`").strip()

    try:
        parsed: dict = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        struct_logger.error("Gemini returned invalid JSON: %s\nRaw: %s", exc, raw_response[:500])
        # Return fallback classification
        return {
            col: {"type": "Safe", "reason": "Classification failed; defaulting to Safe."}
            for col in expected_columns
        }

    result = {}
    for col in expected_columns:
        if col in parsed:
            entry = parsed[col]
            col_type = entry.get("type", "Safe")
            reason = entry.get("reason", "No reason provided.")

            if col_type not in STRUCT_VALID_COLUMN_TYPES:
                struct_logger.warning(
                    "Invalid type '%s' for column '%s'; defaulting to 'Safe'.", col_type, col
                )
                col_type = "Safe"

            result[col] = {"type": col_type, "reason": reason}
        else:
            struct_logger.warning("Column '%s' missing from Gemini response; defaulting to 'Safe'.", col)
            result[col] = {
                "type": "Safe",
                "reason": "Not classified by Gemini; defaulted to Safe.",
            }

    return result


# ─────────────────────────────────────────────
# Handle High Cardinality / Edge Cases Pre-flight
# ─────────────────────────────────────────────
def struct_prefilter_columns(df: pd.DataFrame) -> tuple[list[str], dict]:
    """
    Identify and handle edge-case columns before sending to Gemini:
    - Fully null columns → mark as Safe (no data)
    - Single unique value columns → likely constants, Safe
    - ID-like columns (name ends with 'id', all unique) → Safe

    Args:
        df: Sampled DataFrame.

    Returns:
        Tuple of:
          - columns_to_classify: list of columns to send to Gemini
          - prefiltered: dict of pre-classified columns with reason
    """
    to_classify = []
    prefiltered = {}

    for col in df.columns:
        series = df[col].dropna()

        if series.empty or series.nunique() == 0:
            prefiltered[col] = {
                "type": "Safe",
                "reason": "Column is fully empty or null; excluded from semantic analysis.",
            }
            continue

        if series.nunique() == 1:
            prefiltered[col] = {
                "type": "Safe",
                "reason": f"Column has only one unique value ('{series.iloc[0]}'); likely a constant.",
            }
            continue

        name_lower = col.lower()
        all_unique = series.nunique() == len(series)
        if all_unique and (name_lower.endswith("id") or name_lower.endswith("_id") or name_lower == "id"):
            prefiltered[col] = {
                "type": "Safe",
                "reason": "Column appears to be a unique identifier (ID field); not a modeling feature.",
            }
            continue

        to_classify.append(col)

    return to_classify, prefiltered


def struct_classify_columns(
    table_name: str,
    conn: Optional[sqlite3.Connection] = None,
) -> dict:

    # Step 1: Sample
    sample_df = struct_sample_table(table_name, conn=conn)

    if sample_df.empty:
        struct_logger.warning("Table '%s' is empty. No columns to classify.", table_name)
        return {}

    # Step 2: Prefilter
    columns_to_classify, prefiltered_results = struct_prefilter_columns(sample_df)

    struct_logger.info(
        "Prefiltered %d columns as trivial; sending %d to Groq.",
        len(prefiltered_results), len(columns_to_classify),
    )

    if not columns_to_classify:
        return prefiltered_results

    # Step 3: Build profile
    classify_df = sample_df[columns_to_classify]
    column_profile = struct_build_column_profile(classify_df)

    # Step 4: Send to Groq
    prompt = struct_build_classification_prompt(column_profile)

    try:
        client = struct_get_groq_client()

        struct_logger.info("Sending %d columns to Groq for classification...", len(columns_to_classify))

        response = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a data bias detection expert. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=GROQ_TEMPERATURE,
        )

        raw_text = response.choices[0].message.content

        struct_logger.debug("Groq response (first 500 chars): %s", raw_text[:500])

    except Exception as exc:
        struct_logger.error("Groq API call failed: %s", exc)

        fallback = {
            col: {
                "type": "Safe",
                "reason": f"Groq API unavailable ({exc}). Manual review required.",
            }
            for col in columns_to_classify
        }

        return {**prefiltered_results, **fallback}

    # Step 5: Parse response
    groq_results = struct_parse_gemini_classification(raw_text, columns_to_classify)

    # Step 6: Merge
    combined = {**prefiltered_results, **groq_results}

    struct_logger.info("Column classification complete: %d columns.", len(combined))

    return combined

# ─────────────────────────────────────────────
# Column Mapping Extraction Helpers
# ─────────────────────────────────────────────
def struct_extract_columns_by_type(
    classification: dict, col_type: str
) -> list[str]:
    """
    Extract column names of a specific type from classification results.

    Args:
        classification: Output of struct_classify_columns.
        col_type: One of 'Target', 'Sensitive', 'Proxy', 'Safe'.

    Returns:
        List of column names.
    """
    return [col for col, meta in classification.items() if meta.get("type") == col_type]


def struct_get_sensitive_and_proxy_columns(classification: dict) -> list[str]:
    """
    Return all Sensitive and Proxy columns (both introduce bias risk).

    Args:
        classification: Output of struct_classify_columns.

    Returns:
        List of column names.
    """
    return [
        col
        for col, meta in classification.items()
        if meta.get("type") in {"Sensitive", "Proxy"}
    ]