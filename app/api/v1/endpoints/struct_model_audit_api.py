"""
struct_model_audit_api.py
Module 2 — FastAPI Router: Trained Model Bias Audit Endpoints

Simplified flow — user uploads ONLY model_file + dataset_file.
The system auto-detects:
  - protected columns (via GROQ column classification)
  - target columns (via GROQ column classification)
  - model type (from file extension)
  - session management (auto-generated)

Provides 3 Postman-testable endpoints:
  POST /upload-and-audit  → accepts model + dataset, runs full pipeline
  POST /run-model-audit   → runs audit on already-uploaded data (advanced)
  GET  /audit-report/{job_id} → retrieves a stored audit report

Zero business logic — all orchestration delegated to StructModelAuditService.
"""

import json
import logging
import os
import shutil
import sqlite3
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.struct_local_config import SQLITE_DB_PATH, DATA_DIR
from app.schemas.struct_model_audit_schema import StructModelAuditResponse
from app.services.struct_model_auditor import StructModelAuditService
from app.services.struct_ingestion import struct_ingest_file
from app.services.struct_intelligence import (
    struct_classify_columns,
    struct_extract_columns_by_type,
)

struct_logger = logging.getLogger("struct_model_audit_api")


def _sanitize_for_json(obj):
    """
    Recursively convert numpy/pandas types to native Python types
    so the result is JSON-serializable.
    """
    import numpy as np
    import pandas as pd

    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.str_,)):
        return str(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    elif pd.isna(obj) if isinstance(obj, float) else False:
        return None
    return obj


router = APIRouter()


# ─────────────────────────────────────────────
# POST /upload-and-audit
# The ONE endpoint users need — give model + dataset, get bias verdict
# ─────────────────────────────────────────────
@router.post("/upload-and-audit")
async def upload_and_audit(
    model_file: UploadFile = File(...),
    dataset_file: UploadFile = File(...),
):
    """
    Upload a trained model + dataset and get a full bias audit.
    
    The system automatically:
      1. Ingests the dataset into SQLite
      2. Classifies columns via GROQ (detects sensitive/target)
      3. Detects model type from file extension
      4. Runs the full 5-layer bias audit pipeline
      5. Returns verdict, metrics, SHAP, narrative, governance
    
    Accepts multipart/form-data with:
      - model_file: Trained model (.pkl/.joblib/.h5/.keras/.pt/.pth/.onnx)
      - dataset_file: Dataset (.csv/.json/.xlsx)
    
    Returns: Full StructModelAuditResponse with bias verdict.
    """
    model_path = None
    dataset_path = None

    try:
        # ── Save model file ──
        unique_id = str(uuid4())[:8]
        model_name = model_file.filename or "model.bin"
        model_save_dir = os.path.join(DATA_DIR, "models")
        os.makedirs(model_save_dir, exist_ok=True)
        model_path = os.path.join(model_save_dir, f"{unique_id}_{model_name}")

        model_content = await model_file.read()
        with open(model_path, "wb") as f:
            f.write(model_content)

        struct_logger.info("Model saved: '%s' → '%s'", model_name, model_path)

        # ── Save dataset file ──
        dataset_name = dataset_file.filename or "dataset.csv"
        dataset_path = os.path.join(DATA_DIR, dataset_name)

        dataset_content = await dataset_file.read()
        with open(dataset_path, "wb") as f:
            f.write(dataset_content)

        struct_logger.info("Dataset saved: '%s' → '%s'", dataset_name, dataset_path)

        # ── Step 1: Ingest dataset (reuse Module 1 ingestion) ──
        ingestion_result = struct_ingest_file(dataset_path)
        table_name = ingestion_result.table_name
        struct_logger.info(
            "Dataset ingested: table='%s' (%d rows, %d cols)",
            table_name, ingestion_result.row_count, ingestion_result.column_count,
        )

        # ── Step 2: Classify columns (reuse Module 1 intelligence) ──
        classification = struct_classify_columns(table_name)

        sensitive_columns = struct_extract_columns_by_type(classification, "Sensitive")
        target_columns = struct_extract_columns_by_type(classification, "Target")

        if not sensitive_columns:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No sensitive/protected columns detected in the dataset. "
                    f"Columns found: {list(classification.keys())}. "
                    f"Classifications: {json.dumps({k: v['type'] for k, v in classification.items()})}"
                ),
            )

        if not target_columns:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No target column detected in the dataset. "
                    f"Columns found: {list(classification.keys())}. "
                    f"Classifications: {json.dumps({k: v['type'] for k, v in classification.items()})}"
                ),
            )

        # Auto-select first detected columns
        protected_col = sensitive_columns[0]
        target_col = target_columns[0]

        struct_logger.info(
            "Auto-detected columns — protected: '%s' (from %s), target: '%s' (from %s)",
            protected_col, sensitive_columns, target_col, target_columns,
        )

        # ── Step 3: Detect model type ──
        _, ext = os.path.splitext(model_name.lower())
        model_type_hint = _detect_type_hint(ext)

        # ── Step 4: Run the full audit pipeline ──
        service = StructModelAuditService()
        result = service.run_audit(
            model_path=model_path,
            session_id=table_name,
            protected_col=protected_col,
            target_col=target_col,
            model_type=model_type_hint if model_type_hint != "unknown" else None,
        )

        # Include auto-detection info in response
        response_data = result.model_dump()
        response_data["auto_detected"] = {
            "sensitive_columns": sensitive_columns,
            "target_columns": target_columns,
            "selected_protected_column": protected_col,
            "selected_target_column": target_col,
            "model_type_detected": model_type_hint,
            "table_name": table_name,
            "dataset_rows": ingestion_result.row_count,
            "dataset_columns": ingestion_result.columns,
        }

        # Sanitize any remaining numpy types for JSON serialization
        response_data = _sanitize_for_json(response_data)
        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        struct_logger.error("Upload-and-audit failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Audit failed: {str(e)}",
        )
    finally:
        # Clean up model file
        if model_path and os.path.exists(model_path):
            try:
                os.remove(model_path)
                struct_logger.info("Cleaned up model file: %s", model_path)
            except Exception:
                pass
        # Clean up dataset file (data is already in SQLite)
        if dataset_path and os.path.exists(dataset_path):
            try:
                os.remove(dataset_path)
                struct_logger.info("Cleaned up dataset file: %s", dataset_path)
            except Exception:
                pass


# ─────────────────────────────────────────────
# POST /upload-model (simplified — model only, dataset already uploaded)
# ─────────────────────────────────────────────
@router.post("/upload-model")
async def upload_model(
    model_file: UploadFile = File(...),
    dataset_file: Optional[UploadFile] = File(None),
):
    """
    Upload a model file (and optionally a dataset file).
    Returns model_path and detected info for use with /run-model-audit.
    
    If dataset_file is provided, it will be ingested and columns auto-classified.
    If not, the user must provide session_id (table_name) in /run-model-audit.
    """
    try:
        # Save model file
        unique_id = str(uuid4())[:8]
        model_name = model_file.filename or "model.bin"
        model_save_dir = os.path.join(DATA_DIR, "models")
        os.makedirs(model_save_dir, exist_ok=True)
        model_path = os.path.join(model_save_dir, f"{unique_id}_{model_name}")

        model_content = await model_file.read()
        with open(model_path, "wb") as f:
            f.write(model_content)

        _, ext = os.path.splitext(model_name.lower())
        type_hint = _detect_type_hint(ext)

        response = {
            "model_path": model_path,
            "model_type_hint": type_hint,
            "status": "ready",
        }

        # If dataset is also uploaded, ingest + classify
        if dataset_file:
            dataset_name = dataset_file.filename or "dataset.csv"
            dataset_path = os.path.join(DATA_DIR, dataset_name)

            dataset_content = await dataset_file.read()
            with open(dataset_path, "wb") as f:
                f.write(dataset_content)

            ingestion_result = struct_ingest_file(dataset_path)
            classification = struct_classify_columns(ingestion_result.table_name)

            sensitive_columns = struct_extract_columns_by_type(classification, "Sensitive")
            target_columns = struct_extract_columns_by_type(classification, "Target")

            response["session_id"] = ingestion_result.table_name
            response["sensitive_columns"] = sensitive_columns
            response["target_columns"] = target_columns
            response["dataset_rows"] = ingestion_result.row_count
            response["dataset_columns"] = ingestion_result.columns

            # Suggest first detected columns
            if sensitive_columns:
                response["suggested_protected_column"] = sensitive_columns[0]
            if target_columns:
                response["suggested_target_column"] = target_columns[0]

            # Clean up dataset file (already in SQLite)
            if os.path.exists(dataset_path):
                os.remove(dataset_path)

        struct_logger.info("Model uploaded: '%s' (type=%s)", model_name, type_hint)
        return response

    except Exception as e:
        struct_logger.error("Model upload failed: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


# ─────────────────────────────────────────────
# POST /run-model-audit (advanced — for manual column selection)
# ─────────────────────────────────────────────
@router.post("/run-model-audit", response_model=StructModelAuditResponse)
async def run_model_audit(request: dict):
    """
    Run the full model bias audit pipeline.
    
    Accepts JSON body:
    {
      "model_path": "path from /upload-model response",
      "session_id": "table name from dataset ingestion",
      "protected_column": "sex",
      "target_column": "hired"
    }
    
    Returns: StructModelAuditResponse with bias verdict, metrics,
             SHAP features, AI narrative, and governance output.
    """
    model_path = request.get("model_path")
    session_id = request.get("session_id")
    protected_column = request.get("protected_column")
    target_column = request.get("target_column")

    if not all([model_path, session_id, protected_column, target_column]):
        raise HTTPException(
            status_code=400,
            detail=(
                "Missing required fields. Required: "
                "model_path, session_id, protected_column, target_column"
            ),
        )

    try:
        service = StructModelAuditService()
        result = service.run_audit(
            model_path=model_path,
            session_id=session_id,
            protected_col=protected_column,
            target_col=target_column,
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        struct_logger.error("Model audit failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Model audit failed: {str(e)}")
    finally:
        if model_path and os.path.exists(model_path):
            try:
                os.remove(model_path)
            except Exception:
                pass


# ─────────────────────────────────────────────
# GET /audit-report/{job_id}
# ─────────────────────────────────────────────
@router.get("/audit-report/{job_id}")
async def get_audit_report(job_id: str):
    """
    Retrieve a stored model audit report by job_id.
    
    Returns: Full audit result JSON.
    HTTPException 404 if job_id not found.
    """
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            "SELECT result_json FROM model_audits WHERE job_id = ?",
            (job_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Audit report not found for job_id: '{job_id}'. "
                       f"Run /upload-and-audit first.",
            )

        result = json.loads(row[0])
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        struct_logger.error("Failed to retrieve audit report: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audit report: {str(e)}",
        )


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────
def _detect_type_hint(ext: str) -> str:
    """Map file extension to model type hint."""
    mapping = {
        ".pkl": "sklearn",
        ".joblib": "sklearn",
        ".h5": "tensorflow",
        ".keras": "tensorflow",
        ".pt": "pytorch",
        ".pth": "pytorch",
        ".onnx": "onnx",
    }
    return mapping.get(ext, "unknown")
