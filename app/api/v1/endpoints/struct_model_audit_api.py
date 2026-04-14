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

@router.post("/upload-and-audit")
async def upload_and_audit(
    model_file: UploadFile = File(...),
    dataset_file: UploadFile = File(...),
):
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
