import os
import time
import shutil
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from app.core.struct_local_config import DATA_DIR
from app.services.struct_ingestion import struct_ingest_file
from app.services.struct_intelligence import struct_classify_columns
from app.services.struct_statistics import struct_run_fairness_audit
from app.services.struct_reporting import struct_generate_report

router = APIRouter()
_state = {}

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
async def run_audit():
    if "table_name" not in _state:
        raise HTTPException(status_code=400, detail="No dataset uploaded yet. Call /upload first.")
    try:
        table = _state["table_name"]
        classification = struct_classify_columns(table)
        audit = struct_run_fairness_audit(table, classification)
        # Wait 61s for Groq free-tier TPM rate limit to reset
        time.sleep(61)
        report = struct_generate_report(audit, classification)
        _state["report"] = report
        
        file_path = _state.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return {
            "status": "success",
            "table_audited": table,
            "bias_detected": report.get("bias_detected"),
            "risk_level": report.get("risk_level")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report")
async def get_report():
    if "report" not in _state:
        raise HTTPException(status_code=404, detail="No report available. Run /run-audit first.")
    return JSONResponse(content=_state["report"])

@router.get("/tables")
async def list_tables():
    from app.services.struct_ingestion import struct_list_tables
    return {"tables": struct_list_tables()}