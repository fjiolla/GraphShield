import json
import sqlite3
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.core.struct_local_config import SQLITE_DB_PATH

router = APIRouter()


def _get_db_connection():
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/audits", response_model=List[Dict[str, Any]])
async def list_audits():
    """
    Returns a list of all historical audits across the system.
    Combines model_audits and audit_sessions tables.
    """
    try:
        conn = _get_db_connection()
        audits = []

        # ── Model Audits ──
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_audits'")
        if cursor.fetchone():
            cursor = conn.execute(
                "SELECT job_id, session_id, result_json, timestamp FROM model_audits ORDER BY timestamp DESC"
            )
            for row in cursor.fetchall():
                try:
                    result_data = json.loads(row["result_json"]) if row["result_json"] else {}
                    score = 0
                    status = "neutral"
                    if "governance" in result_data:
                        score = result_data["governance"].get("overall_fairness_score", 0)
                    if "verdict" in result_data:
                        verdict_str = result_data["verdict"].get("bias_verdict", "NEUTRAL").upper()
                        if verdict_str in ("FAIR",): status = "pass"
                        elif verdict_str == "MARGINAL": status = "warn"
                        elif verdict_str == "BIASED": status = "fail"

                    audits.append({
                        "id": row["job_id"],
                        "type": "Model Audit",
                        "target": row["session_id"] or "Unknown Model",
                        "date": row["timestamp"],
                        "status": status,
                        "score": score,
                        "raw_result": result_data,
                    })
                except Exception:
                    continue

        # ── Dataset (Struct) Audits ──
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_sessions'")
        if cursor.fetchone():
            cursor = conn.execute(
                "SELECT session_id, table_name, report_json, created_at FROM audit_sessions ORDER BY created_at DESC"
            )
            for row in cursor.fetchall():
                try:
                    report_data = json.loads(row["report_json"]) if row["report_json"] else {}
                    risk = report_data.get("risk_level", "")
                    if risk == "High": status = "fail"
                    elif risk == "Medium": status = "warn"
                    elif risk == "Low": status = "pass"
                    else: status = "neutral"

                    audits.append({
                        "id": row["session_id"],
                        "type": "Dataset Audit",
                        "target": row["table_name"] or row["session_id"],
                        "date": row["created_at"],
                        "status": status,
                        "score": 0,
                        "raw_result": report_data,
                    })
                except Exception:
                    continue

        # ── Document Audits ──
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_audits'")
        if cursor.fetchone():
            cursor = conn.execute(
                "SELECT session_id, filename, result_json, timestamp FROM document_audits ORDER BY timestamp DESC"
            )
            for row in cursor.fetchall():
                try:
                    result_data = json.loads(row["result_json"]) if row["result_json"] else {}
                    
                    status = "neutral"
                    qualitative = result_data.get("findings", {}).get("qualitative_analysis", {})
                    dynamic_profile = qualitative.get("dynamic_profile", {})
                    groups = dynamic_profile.get("groups", [])
                    
                    if groups:
                        has_explicit = any(g.get("bias_type") == "explicit" for g in groups)
                        status = "fail" if has_explicit else "warn"
                    else:
                        status = "pass"

                    audits.append({
                        "id": row["session_id"],
                        "type": "Document Audit",
                        "target": row["filename"] or "Unknown Document",
                        "date": row["timestamp"],
                        "status": status,
                        "score": 0,
                        "raw_result": result_data,
                    })
                except Exception:
                    continue

        # Sort all by date descending
        audits.sort(key=lambda x: x.get("date") or "", reverse=True)
        return audits

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
