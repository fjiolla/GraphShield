"""
struct_sql_transpiler.py
PostgreSQL → SQLite SQL transpilation utility.

Converts PostgreSQL pg_dump output into SQLite-compatible SQL by:
- Stripping unsupported commands (SET, CREATE EXTENSION, CREATE SEQUENCE, etc.)
- Removing schema prefixes (public.table_name → table_name)
- Converting PostgreSQL types → SQLite types
- Converting boolean literals (TRUE/FALSE → 1/0)
- Smart statement splitting (respects quoted strings)
- Extracting table names from CREATE TABLE statements
"""

import logging
import re

struct_logger = logging.getLogger("struct_sql_transpiler")

# ─────────────────────────────────────────────
# PostgreSQL commands to strip entirely
# ─────────────────────────────────────────────
_PG_SKIP_PATTERNS = [
    # SET commands
    re.compile(r"^\s*SET\s+", re.IGNORECASE),
    # CREATE EXTENSION
    re.compile(r"^\s*CREATE\s+EXTENSION\s+", re.IGNORECASE),
    # CREATE SEQUENCE
    re.compile(r"^\s*CREATE\s+SEQUENCE\s+", re.IGNORECASE),
    # ALTER SEQUENCE
    re.compile(r"^\s*ALTER\s+SEQUENCE\s+", re.IGNORECASE),
    # SELECT pg_catalog.*
    re.compile(r"^\s*SELECT\s+pg_catalog\.", re.IGNORECASE),
    # ALTER TABLE ... SET DEFAULT nextval(...)
    re.compile(r"^\s*ALTER\s+TABLE\s+.*SET\s+DEFAULT\s+nextval\s*\(", re.IGNORECASE),
    # ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY
    re.compile(r"^\s*ALTER\s+TABLE\s+.*ADD\s+CONSTRAINT\s+.*FOREIGN\s+KEY", re.IGNORECASE),
    # ALTER TABLE ... ADD CONSTRAINT ... PRIMARY KEY
    re.compile(r"^\s*ALTER\s+TABLE\s+.*ADD\s+CONSTRAINT\s+.*PRIMARY\s+KEY", re.IGNORECASE),
    # ALTER TABLE ONLY ... ALTER COLUMN ... SET DEFAULT
    re.compile(r"^\s*ALTER\s+TABLE\s+ONLY\s+", re.IGNORECASE),
]

# ─────────────────────────────────────────────
# PostgreSQL type → SQLite type mapping
# ─────────────────────────────────────────────
_PG_TYPE_MAP = [
    (re.compile(r"\bcharacter\s+varying\s*\(\d+\)", re.IGNORECASE), "TEXT"),
    (re.compile(r"\bvarchar\s*\(\d+\)", re.IGNORECASE), "TEXT"),
    (re.compile(r"\bcharacter\s*\(\d+\)", re.IGNORECASE), "TEXT"),
    (re.compile(r"\bchar\s*\(\d+\)", re.IGNORECASE), "TEXT"),
    (re.compile(r"\bnumeric\s*\(\d+\s*,\s*\d+\)", re.IGNORECASE), "REAL"),
    (re.compile(r"\bnumeric\s*\(\d+\)", re.IGNORECASE), "REAL"),
    (re.compile(r"\bnumeric\b", re.IGNORECASE), "REAL"),
    (re.compile(r"\bdecimal\s*\(\d+\s*,\s*\d+\)", re.IGNORECASE), "REAL"),
    (re.compile(r"\bdecimal\s*\(\d+\)", re.IGNORECASE), "REAL"),
    (re.compile(r"\btimestamp\s+without\s+time\s+zone\b", re.IGNORECASE), "TEXT"),
    (re.compile(r"\btimestamp\s+with\s+time\s+zone\b", re.IGNORECASE), "TEXT"),
    (re.compile(r"\btimestamp\b", re.IGNORECASE), "TEXT"),
    (re.compile(r"\bboolean\b", re.IGNORECASE), "INTEGER"),
    (re.compile(r"\bbigint\b", re.IGNORECASE), "INTEGER"),
    (re.compile(r"\bsmallint\b", re.IGNORECASE), "INTEGER"),
    (re.compile(r"\bserial\b", re.IGNORECASE), "INTEGER"),
    (re.compile(r"\bbigserial\b", re.IGNORECASE), "INTEGER"),
    (re.compile(r"\bdouble\s+precision\b", re.IGNORECASE), "REAL"),
    (re.compile(r"\bfloat\b", re.IGNORECASE), "REAL"),
    (re.compile(r"\bjsonb?\b", re.IGNORECASE), "TEXT"),
    (re.compile(r"\buuid\b", re.IGNORECASE), "TEXT"),
    (re.compile(r"\bbytea\b", re.IGNORECASE), "BLOB"),
]


# ─────────────────────────────────────────────
# Smart Statement Splitting
# ─────────────────────────────────────────────
def _smart_split_statements(sql: str) -> list[str]:
    """
    Split SQL text on semicolons, but respect single-quoted strings.
    Handles: INSERT INTO t VALUES ('hello; world');
    """
    statements = []
    current = []
    in_quote = False

    for char in sql:
        if char == "'" and not in_quote:
            in_quote = True
            current.append(char)
        elif char == "'" and in_quote:
            in_quote = False
            current.append(char)
        elif char == ";" and not in_quote:
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(char)

    # Handle last statement without trailing semicolon
    last = "".join(current).strip()
    if last:
        statements.append(last)

    return statements


# ─────────────────────────────────────────────
# Comment Stripping
# ─────────────────────────────────────────────
def _strip_comments(sql: str) -> str:
    """Remove SQL line comments (-- ...) and blank lines."""
    lines = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        # Remove inline comments (but not inside quotes)
        if "--" in line and "'" not in line:
            line = line[:line.index("--")]
        lines.append(line)
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Schema Prefix Removal
# ─────────────────────────────────────────────
def _remove_schema_prefix(sql: str) -> str:
    """Remove 'public.' schema prefix from all table references."""
    return re.sub(r"\bpublic\.", "", sql, flags=re.IGNORECASE)


# ─────────────────────────────────────────────
# PostgreSQL Type Conversion
# ─────────────────────────────────────────────
def _convert_pg_types(sql: str) -> str:
    """Convert PostgreSQL column types to SQLite types."""
    for pattern, sqlite_type in _PG_TYPE_MAP:
        sql = pattern.sub(sqlite_type, sql)
    return sql


# ─────────────────────────────────────────────
# Boolean Literal Conversion
# ─────────────────────────────────────────────
def _convert_pg_booleans(sql: str) -> str:
    """
    Convert PostgreSQL boolean literals TRUE/FALSE → 1/0 in INSERT statements.
    Only converts when TRUE/FALSE appear as standalone values (not inside strings).
    """
    # Match TRUE/FALSE as whole words, not inside quotes
    # Process line-by-line to only affect INSERT statements
    lines = []
    for line in sql.splitlines():
        upper = line.strip().upper()
        if upper.startswith("INSERT"):
            # Replace TRUE/FALSE outside quotes
            result = []
            in_quote = False
            i = 0
            while i < len(line):
                if line[i] == "'":
                    in_quote = not in_quote
                    result.append(line[i])
                    i += 1
                elif not in_quote:
                    # Check for TRUE
                    if line[i:i+4].upper() == "TRUE" and (i + 4 >= len(line) or not line[i+4].isalnum()):
                        if i == 0 or not line[i-1].isalnum():
                            result.append("1")
                            i += 4
                            continue
                    # Check for FALSE
                    if line[i:i+5].upper() == "FALSE" and (i + 5 >= len(line) or not line[i+5].isalnum()):
                        if i == 0 or not line[i-1].isalnum():
                            result.append("0")
                            i += 5
                            continue
                    result.append(line[i])
                    i += 1
                else:
                    result.append(line[i])
                    i += 1
            lines.append("".join(result))
        else:
            lines.append(line)
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Statement Filtering
# ─────────────────────────────────────────────
def _should_skip_statement(stmt: str) -> bool:
    """Check if a SQL statement should be skipped (PostgreSQL-specific)."""
    for pattern in _PG_SKIP_PATTERNS:
        if pattern.search(stmt):
            return True
    return False


# ─────────────────────────────────────────────
# Table Name Extraction
# ─────────────────────────────────────────────
def _extract_table_names(sql: str) -> list[str]:
    """Extract table names from CREATE TABLE statements."""
    # Match CREATE TABLE [IF NOT EXISTS] table_name
    pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)",
        re.IGNORECASE,
    )
    return pattern.findall(sql)


# ─────────────────────────────────────────────
# Primary Transpiler Entrypoint
# ─────────────────────────────────────────────
def struct_transpile_sql(raw_sql: str) -> tuple[list[str], list[str]]:
    """
    Transpile PostgreSQL SQL to SQLite-compatible SQL.

    Pipeline:
    1. Strip comments
    2. Remove schema prefixes (public.)
    3. Convert PostgreSQL types → SQLite types
    4. Convert boolean literals (TRUE/FALSE → 1/0)
    5. Smart-split into individual statements
    6. Filter out unsupported PostgreSQL commands
    7. Extract table names from CREATE TABLE statements

    Args:
        raw_sql: Raw SQL text (potentially from pg_dump).

    Returns:
        Tuple of:
        - List of SQLite-compatible SQL statements
        - List of table names found in CREATE TABLE statements
    """
    struct_logger.info("Starting SQL transpilation (%d chars).", len(raw_sql))

    # Step 1: Strip comments
    sql = _strip_comments(raw_sql)

    # Step 2: Remove schema prefix
    sql = _remove_schema_prefix(sql)

    # Step 3: Convert types
    sql = _convert_pg_types(sql)

    # Step 4: Convert booleans
    sql = _convert_pg_booleans(sql)

    # Step 5: Extract table names before splitting
    table_names = _extract_table_names(sql)
    struct_logger.info("Found %d CREATE TABLE statements: %s", len(table_names), table_names)

    # Step 6: Smart-split into statements
    all_statements = _smart_split_statements(sql)

    # Step 7: Filter out unsupported commands
    valid_statements = []
    skipped_count = 0
    for stmt in all_statements:
        if _should_skip_statement(stmt):
            skipped_count += 1
            struct_logger.debug("Skipped PG-specific statement: %s...", stmt[:60])
        else:
            valid_statements.append(stmt)

    struct_logger.info(
        "Transpilation complete: %d valid statements, %d skipped, %d tables.",
        len(valid_statements), skipped_count, len(table_names),
    )

    return valid_statements, table_names
