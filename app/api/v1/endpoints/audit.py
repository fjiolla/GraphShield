from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.localextraction import extract_text_from_file
from app.services.analysis import perform_dynamic_bias_profiling
from app.services.vector_audit import verify_contextual_bias
from app.services.remediation import generate_remediation_plan
from app.core.struct_local_config import SQLITE_DB_PATH
import sqlite3
import json
from datetime import datetime, timezone
import uuid
import logging

router = APIRouter()
logger = logging.getLogger("document_audit_api")

def _persist_document_audit(filename: str, result_dict: dict) -> None:
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_audits (
                session_id TEXT PRIMARY KEY,
                filename TEXT,
                result_json TEXT,
                timestamp TEXT
            )
        """)
        session_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO document_audits (session_id, filename, result_json, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, filename, json.dumps(result_dict), datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning("Failed to persist document audit: %s", e)


@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    valid_types = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload PDF, TXT, or DOCX.")

    try:
        content = await file.read()
        extracted_text = await extract_text_from_file(
            content,
            file.content_type
        )

        bias_results = await perform_dynamic_bias_profiling(extracted_text)
        print(bias_results)

        # Guard: if LLM parsing failed, bias_results won't have a "dynamic_profile" key
        if "error" in bias_results or "dynamic_profile" not in bias_results:
            detail = bias_results.get("details", bias_results.get("error", "Bias profiling failed — LLM returned an unexpected response."))
            raise HTTPException(status_code=502, detail=str(detail))

        if "groups" in bias_results["dynamic_profile"]:
            quantitative_audit = await verify_contextual_bias(
                extracted_text, 
                bias_results["dynamic_profile"]["groups"]
            )
        else:
            quantitative_audit = []
        print("first setp is doen!!!")    

        recommendation = await generate_remediation_plan(bias_results["dynamic_profile"])
        
        final_result = {
            "filename": file.filename,
            "audit_metadata": {
                "engine_v": "2.0-contextual",
                "status": "Verified"
            },
            "findings": {
                "qualitative_analysis": bias_results,
                "quantitative_verification": quantitative_audit
            },
            "recommendation": recommendation
        }
        
        # Save to database so it shows up on the Overview dashboard
        _persist_document_audit(file.filename, final_result)
        
        return final_result
        
    except Exception as e:
        print("This is an error into backend!!",e)
        raise HTTPException(status_code=500, detail=str(e))
    
    
    