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

struct_logger = logging.getLogger("struct_ingestion")

def struct_get_db_connection() -> sqlite3.Connection:
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    struct_logger.debug("SQLite connection opened: %s", SQLITE_DB_PATH)
    return conn



def struct_write_to_sqlite(
    df: pd.DataFrame,
    table_name: str,
    conn: Optional[sqlite3.Connection] = None,
    if_exists: str = "replace",
) -> str:
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


def struct_ingest_csv(file_path: Path) -> pd.DataFrame:
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
    encoding = struct_detect_encoding(file_path)
    with open(file_path, encoding=encoding) as fh:
        sql_text = fh.read().strip()

    if not sql_text:
        raise ValueError(f"SQL file '{file_path.name}' is empty.")

    _conn = conn or struct_get_db_connection()
    close_after = conn is None

    try:
        cursor = _conn.cursor()

        # Split on semicolons; handle multiple statements
        statements = [s.strip() for s in sql_text.split(";") if s.strip()]

        last_select_df = pd.DataFrame()
        for stmt in statements:
            upper = stmt.upper().lstrip()
            if upper.startswith("SELECT"):
                last_select_df = pd.read_sql_query(stmt, _conn)
                struct_logger.info("SQL SELECT returned %d rows.", len(last_select_df))
            else:
                cursor.execute(stmt)
                struct_logger.info("SQL executed: %s...", stmt[:60])

        _conn.commit()
        return struct_sanitize_dataframe(last_select_df) if not last_select_df.empty else last_select_df

    except Exception as exc:
        raise RuntimeError(f"SQL execution failed for '{file_path.name}': {exc}") from exc
    finally:
        if close_after:
            _conn.close()


def struct_ingest_xlsx(file_path: Path) -> pd.DataFrame:
    df = struct_xlsx_to_dataframe(file_path)

    if df.empty:
        raise ValueError(f"Excel file '{file_path.name}' produced an empty DataFrame.")

    df = struct_sanitize_dataframe(df)
    struct_logger.info("XLSX ingested: %s (%d rows, %d cols).", file_path.name, len(df), len(df.columns))
    return df



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
    ):
        self.table_name = table_name
        self.row_count = row_count
        self.column_count = column_count
        self.columns = columns
        self.format_detected = format_detected
        self.file_name = file_name

    def to_dict(self) -> dict:
        return {
            "table_name": self.table_name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": self.columns,
            "format_detected": self.format_detected,
            "file_name": self.file_name,
        }

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
        df = struct_ingest_sql(file_path, conn=conn)
        # SQL files execute on DB directly; may return empty DF (DDL/DML)
        result_table = table_name or struct_safe_table_name(file_path.stem)
        return StructIngestionResult(
            table_name=result_table,
            row_count=len(df),
            column_count=len(df.columns),
            columns=list(df.columns),
            format_detected=fmt,
            file_name=file_path.name,
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


def struct_list_tables(conn: Optional[sqlite3.Connection] = None) -> list[str]:
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

    _conn = conn or struct_get_db_connection()
    close_after = conn is None
    try:
        cursor = _conn.execute(f"PRAGMA table_info('{table_name}');")
        cols = ["cid", "name", "type", "notnull", "dflt_value", "pk"]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    finally:
        if close_after:
            _conn.close()