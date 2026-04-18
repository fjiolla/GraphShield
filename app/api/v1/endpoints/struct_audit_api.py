import json
import os
import sqlite3
import time
import shutil
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, File, Query, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from app.core.struct_local_config import DATA_DIR, SQLITE_DB_PATH
from app.services.struct_ingestion import struct_ingest_file
from app.services.struct_intelligence import struct_classify_columns
from app.services.struct_statistics import struct_run_fairness_audit
from app.services.struct_reporting import struct_generate_report

router = APIRouter()
_state: dict = {}


def _persist_audit_session(session_id: str, table_name: str, report: dict) -> None:
    """Write dataset audit result to SQLite so it survives restarts and appears in Audit Trail."""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_sessions (
                session_id TEXT PRIMARY KEY,
                table_name TEXT,
                report_json TEXT,
                dataset_path TEXT,
                created_at TEXT
            )
        """)
        conn.execute(
            "INSERT OR REPLACE INTO audit_sessions (session_id, table_name, report_json, dataset_path, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, table_name, json.dumps(report), "", datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        import logging
        logging.getLogger("struct_audit_api").warning("Failed to persist audit session: %s", e)


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    try:
        save_path = os.path.join(DATA_DIR, file.filename)
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        result = struct_ingest_file(save_path)
        _state["table_name"] = result.table_name
        _state["file_path"] = save_path
        return {"status": "success", "ingestion": result.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/run-audit")
async def run_audit(table_name: str = Query(None, description="Table name from the upload step")):
    # Accept table_name from query param (stateless) OR fall back to in-memory state
    table = table_name or _state.get("table_name")
    if not table:
        raise HTTPException(status_code=400, detail="No dataset uploaded yet. Call /upload first or pass table_name as a query param.")
    try:
        classification = struct_classify_columns(table)
        audit = struct_run_fairness_audit(table, classification)
        # Wait 61s for Groq free-tier TPM rate limit to reset
        time.sleep(61)
        report = struct_generate_report(audit, classification)
        _state["report"] = report

        # Persist to SQLite so it survives restarts and appears in Audit Trail / Analytics
        session_id = str(uuid4())
        _persist_audit_session(session_id, table, report)

        file_path = _state.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return {
            "status": "success",
            "table_audited": table,
            "bias_detected": report.get("bias_detected"),
            "risk_level": report.get("risk_level")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_report():
    # First try in-memory state (fast, same-process)
    if "report" in _state:
        return JSONResponse(content=_state["report"])
    
    # Fallback: read the most recent report from SQLite (survives restarts)
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        cursor = conn.execute(
            "SELECT report_json FROM audit_sessions ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return JSONResponse(content=json.loads(row[0]))
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="No report available. Run /run-audit first.")


@router.get("/tables")
async def list_tables():
    from app.services.struct_ingestion import struct_list_tables
    return {"tables": struct_list_tables()}