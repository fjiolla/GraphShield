"""
struct_ingestion.py
Module 1: Multi-Format Data Ingestion
Handles CSV, JSON, SQL, and XLSX files.
Parses, validates, sanitizes, and persists data to SQLite (local_vault.db).

Future Migration Note:
  Replace SQLite write logic with BigQuery `load_table_from_dataframe`
  or GCS upload + BQ external table with minimal changes.
"""

import json
import logging
import re
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

from app.core.struct_local_config import SQLITE_DB_PATH, DATA_DIR
from app.utils.struct_format_utils import (
    struct_detect_encoding,
    struct_detect_mime,
    struct_json_to_dataframe,
    struct_resolve_format,
    struct_safe_table_name,
    struct_sanitize_dataframe,
    struct_xlsx_to_dataframe,
)
from app.utils.struct_sql_transpiler import struct_transpile_sql

struct_logger = logging.getLogger("struct_ingestion")


# ─────────────────────────────────────────────
# SQLite Connection
# ─────────────────────────────────────────────
def struct_get_db_connection() -> sqlite3.Connection:
    """
    Open and return a SQLite connection to local_vault.db.
    Enables WAL mode and foreign key support to simulate BigQuery robustness.

    Future Migration: Replace with BigQuery client initialization.

    Returns:
        sqlite3.Connection
    """
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    struct_logger.debug("SQLite connection opened: %s", SQLITE_DB_PATH)
    return conn


# ─────────────────────────────────────────────
# Write DataFrame → SQLite
# ─────────────────────────────────────────────
def struct_write_to_sqlite(
    df: pd.DataFrame,
    table_name: str,
    conn: Optional[sqlite3.Connection] = None,
    if_exists: str = "replace",
) -> str:
    """
    Write a pandas DataFrame to a SQLite table.

    Args:
        df: DataFrame to write.
        table_name: Target SQLite table name.
        conn: Optional existing connection. Opens a new one if None.
        if_exists: 'replace' | 'append' | 'fail' (passed to pandas).

    Returns:
        Canonical table name used for writing.

    Raises:
        ValueError: If the DataFrame is empty.
        RuntimeError: On SQLite write failure.

    Future Migration:
        Replace with:
            bq_client.load_table_from_dataframe(df, f"{DATASET}.{table_name}")
    """
    if df is None or df.empty:
        raise ValueError("Cannot write an empty DataFrame to SQLite.")

    safe_name = struct_safe_table_name(table_name)
    _conn = conn or struct_get_db_connection()
    close_after = conn is None

    try:
        df.to_sql(safe_name, _conn, if_exists=if_exists, index=False)
        _conn.commit()
        struct_logger.info(
            "Written %d rows × %d cols to SQLite table '%s'.",
            len(df), len(df.columns), safe_name,
        )
        return safe_name
    except Exception as exc:
        raise RuntimeError(f"SQLite write failed for table '{safe_name}': {exc}") from exc
    finally:
        if close_after:
            _conn.close()


# ─────────────────────────────────────────────
# Format Handlers
# ─────────────────────────────────────────────
def struct_ingest_csv(file_path: Path) -> pd.DataFrame:
    """
    Parse a CSV file into a sanitized DataFrame.
    Auto-detects encoding via chardet.

    Args:
        file_path: Path to the CSV file.

    Returns:
        pandas DataFrame.

    Raises:
        ValueError: If the CSV cannot be parsed or is empty.
    """
    encoding = struct_detect_encoding(file_path)
    try:
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            low_memory=False,
            on_bad_lines="warn",
        )
    except UnicodeDecodeError:
        struct_logger.warning("Encoding '%s' failed; retrying with latin-1.", encoding)
        df = pd.read_csv(file_path, encoding="latin-1", low_memory=False, on_bad_lines="warn")

    if df.empty:
        raise ValueError(f"CSV file '{file_path.name}' is empty or malformed.")

    df = struct_sanitize_dataframe(df)
    struct_logger.info("CSV ingested: %s (%d rows, %d cols).", file_path.name, len(df), len(df.columns))
    return df


def struct_ingest_json(file_path: Path) -> pd.DataFrame:
    """
    Parse a JSON file into a sanitized DataFrame.
    Recursively flattens nested structures using dot-notation.

    Args:
        file_path: Path to the JSON file.

    Returns:
        pandas DataFrame.

    Raises:
        ValueError: If the JSON is invalid or unparseable.
    """
    encoding = struct_detect_encoding(file_path)
    try:
        with open(file_path, encoding=encoding) as fh:
            raw = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in '{file_path.name}': {exc}") from exc

    df = struct_json_to_dataframe(raw)

    if df.empty:
        raise ValueError(f"JSON file '{file_path.name}' produced an empty DataFrame.")

    df = struct_sanitize_dataframe(df)
    struct_logger.info("JSON ingested: %s (%d rows, %d cols).", file_path.name, len(df), len(df.columns))
    return df


def struct_ingest_sql(file_path: Path, conn: Optional[sqlite3.Connection] = None) -> pd.DataFrame:
    """
    Ingest a SQL file by transpiling PostgreSQL → SQLite, executing statements,
    and returning info about all tables created.

    Args:
        file_path: Path to the .sql file.
        conn: Optional existing connection.

    Returns:
        Tuple of (primary_table_name, available_tables_info_list).

    Raises:
        ValueError: If the SQL file is empty or creates no tables.
        RuntimeError: On SQL execution failure.
    """
    encoding = struct_detect_encoding(file_path)
    with open(file_path, encoding=encoding) as fh:
        raw_sql = fh.read().strip()

    if not raw_sql:
        raise ValueError(f"SQL file '{file_path.name}' is empty.")

    # Transpile PostgreSQL → SQLite
    statements, declared_tables = struct_transpile_sql(raw_sql)

    if not statements:
        raise ValueError(f"SQL file '{file_path.name}' has no executable statements after transpilation.")

    _conn = conn or struct_get_db_connection()
    close_after = conn is None

    try:
        cursor = _conn.cursor()

        # Execute all transpiled statements
        for stmt in statements:
            try:
                cursor.execute(stmt)
                struct_logger.debug("SQL OK: %s...", stmt[:80])
            except Exception as stmt_exc:
                struct_logger.warning("SQL statement failed (skipping): %s... | Error: %s", stmt[:80], stmt_exc)
                continue

        _conn.commit()

        # Discover all tables that now exist in the database
        tables_cursor = _conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        all_db_tables = [row[0] for row in tables_cursor.fetchall()]

        # Filter to only tables declared in this SQL file (if we detected any)
        if declared_tables:
            # Match declared names (lowercased) against actual DB tables
            declared_lower = {t.lower() for t in declared_tables}
            relevant_tables = [t for t in all_db_tables if t.lower() in declared_lower]
        else:
            relevant_tables = all_db_tables

        if not relevant_tables:
            raise ValueError(
                f"SQL file '{file_path.name}' did not create any tables. "
                f"Declared: {declared_tables}, DB tables: {all_db_tables}"
            )

        # Build info for each table
        available_tables = []
        for tbl in relevant_tables:
            try:
                row_count = _conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
                col_cursor = _conn.execute(f"PRAGMA table_info([{tbl}])")
                columns = [row[1] for row in col_cursor.fetchall()]
                available_tables.append({
                    "name": tbl,
                    "row_count": row_count,
                    "column_count": len(columns),
                    "columns": columns,
                })
            except Exception as tbl_exc:
                struct_logger.warning("Could not inspect table '%s': %s", tbl, tbl_exc)

        # Sort by row count descending (largest first)
        available_tables.sort(key=lambda t: t["row_count"], reverse=True)

        struct_logger.info(
            "SQL ingested: %s → %d tables created: %s",
            file_path.name, len(available_tables),
            [(t['name'], t['row_count']) for t in available_tables],
        )

        return available_tables

    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"SQL execution failed for '{file_path.name}': {exc}") from exc
    finally:
        if close_after:
            _conn.close()


def struct_ingest_xlsx(file_path: Path) -> pd.DataFrame:
    """
    Parse an Excel (.xlsx) file into a sanitized DataFrame.
    Handles merged cells, auto-detected headers, and Excel serial dates.

    Args:
        file_path: Path to the .xlsx file.

    Returns:
        pandas DataFrame.

    Raises:
        ValueError: If the file is not valid Excel or is empty.
    """
    df = struct_xlsx_to_dataframe(file_path)

    if df.empty:
        raise ValueError(f"Excel file '{file_path.name}' produced an empty DataFrame.")

    df = struct_sanitize_dataframe(df)
    struct_logger.info("XLSX ingested: %s (%d rows, %d cols).", file_path.name, len(df), len(df.columns))
    return df


# ─────────────────────────────────────────────
# Primary Ingestion Entrypoint
# ─────────────────────────────────────────────
class StructIngestionResult:
    """Container for the result of a struct_ingest_file call."""

    def __init__(
        self,
        table_name: str,
        row_count: int,
        column_count: int,
        columns: list[str],
        format_detected: str,
        file_name: str,
        available_tables: Optional[list[dict]] = None,
    ):
        self.table_name = table_name
        self.row_count = row_count
        self.column_count = column_count
        self.columns = columns
        self.format_detected = format_detected
        self.file_name = file_name
        self.available_tables = available_tables

    def to_dict(self) -> dict:
        result = {
            "table_name": self.table_name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": self.columns,
            "format_detected": self.format_detected,
            "file_name": self.file_name,
        }
        if self.available_tables:
            result["available_tables"] = self.available_tables
        return result

    def __repr__(self) -> str:
        return (
            f"StructIngestionResult(table='{self.table_name}', "
            f"rows={self.row_count}, cols={self.column_count}, "
            f"format='{self.format_detected}')"
        )


def struct_ingest_file(
    file_path: str | Path,
    table_name: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> StructIngestionResult:
    """
    Primary ingestion entrypoint.
    Detects file format via MIME type and routes to the appropriate handler.
    Stores parsed data into SQLite (local_vault.db).

    Args:
        file_path: Path to the uploaded file.
        table_name: Optional override for the SQLite table name.
                    Defaults to the sanitized filename stem.
        conn: Optional shared SQLite connection.

    Returns:
        StructIngestionResult with metadata about the ingested data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or data is empty.
        RuntimeError: On ingestion or write failure.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # MIME-based routing
    mime_type = struct_detect_mime(file_path)
    ext = file_path.suffix.lstrip(".")
    fmt = struct_resolve_format(mime_type, ext)

    struct_logger.info(
        "Ingesting '%s' as format='%s' (MIME='%s').", file_path.name, fmt, mime_type
    )

    df: pd.DataFrame

    if fmt == "csv":
        df = struct_ingest_csv(file_path)

    elif fmt == "json":
        df = struct_ingest_json(file_path)

    elif fmt == "sql":
        available_tables = struct_ingest_sql(file_path, conn=conn)
        # Pick the largest table as primary
        primary = available_tables[0] if available_tables else None
        if not primary:
            raise ValueError(f"SQL file '{file_path.name}' created no tables with data.")

        return StructIngestionResult(
            table_name=primary["name"],
            row_count=primary["row_count"],
            column_count=primary["column_count"],
            columns=primary["columns"],
            format_detected=fmt,
            file_name=file_path.name,
            available_tables=available_tables,
        )

    elif fmt == "xlsx":
        df = struct_ingest_xlsx(file_path)

    else:
        raise ValueError(
            f"Unsupported file format '{fmt}' (MIME='{mime_type}') "
            f"for file '{file_path.name}'. "
            f"Supported: CSV, JSON, SQL, XLSX."
        )

    # Derive table name
    target_table = table_name or struct_safe_table_name(file_path.stem)

    # Write to SQLite
    written_table = struct_write_to_sqlite(df, target_table, conn=conn)

    return StructIngestionResult(
        table_name=written_table,
        row_count=len(df),
        column_count=len(df.columns),
        columns=list(df.columns),
        format_detected=fmt,
        file_name=file_path.name,
    )


# ─────────────────────────────────────────────
# Utility: List tables in local_vault.db
# ─────────────────────────────────────────────
def struct_list_tables(conn: Optional[sqlite3.Connection] = None) -> list[str]:
    """
    Return a list of all user tables in the local SQLite database.

    Args:
        conn: Optional connection.

    Returns:
        List of table name strings.
    """
    _conn = conn or struct_get_db_connection()
    close_after = conn is None
    try:
        cursor = _conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        if close_after:
            _conn.close()


def struct_get_table_schema(
    table_name: str, conn: Optional[sqlite3.Connection] = None
) -> list[dict]:
    """
    Return column schema for a SQLite table.

    Args:
        table_name: Table to inspect.
        conn: Optional connection.

    Returns:
        List of dicts with keys: cid, name, type, notnull, dflt_value, pk.
    """
    _conn = conn or struct_get_db_connection()
    close_after = conn is None
    try:
        cursor = _conn.execute(f"PRAGMA table_info('{table_name}');")
        cols = ["cid", "name", "type", "notnull", "dflt_value", "pk"]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    finally:
        if close_after:
            _conn.close()