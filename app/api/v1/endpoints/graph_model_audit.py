"""
FastAPI Router for Graph Bias Pipeline.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import os
import tempfile
import logging
from time import time

from app.graph_model.pipeline import run_graph_bias_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Graph Bias Audit"])

def save_upload_to_temp(upload_file: UploadFile) -> str:
    """Save an UploadFile to a temporary file and return path."""
    if not upload_file or not upload_file.filename:
        return None
        
    ext = os.path.splitext(upload_file.filename)[1]
    fd, path = tempfile.mkstemp(suffix=ext)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(upload_file.file.read())
    except Exception as e:
        os.remove(path)
        raise e
    return path

@router.post("/analyze")
async def analyze_graph_bias(
    background_tasks: BackgroundTasks,
    graph_file: UploadFile = File(...),
    nodes_csv: Optional[UploadFile] = File(None),
    edges_csv: Optional[UploadFile] = File(None),
    predictions_csv: Optional[UploadFile] = File(None),
    model_file: Optional[UploadFile] = File(None),
    feature_csv: Optional[UploadFile] = File(None),
    format: str = Form(...),
    protected_attr: Optional[str] = Form(None),
    prediction_source: str = Form(...),
    prediction_col: Optional[str] = Form(None),
    ground_truth_col: Optional[str] = Form(None),
    domain: Optional[str] = Form(None)
):
    """
    Endpoint to trigger a graph fairness audit.
    """
    start_time = time()
    files_to_cleanup = []
    
    try:
        graph_path = save_upload_to_temp(graph_file)
        if graph_path: files_to_cleanup.append(graph_path)
        
        nodes_path = save_upload_to_temp(nodes_csv)
        if nodes_path: files_to_cleanup.append(nodes_path)
            
        edges_path = save_upload_to_temp(edges_csv)
        if edges_path: files_to_cleanup.append(edges_path)
            
        preds_path = save_upload_to_temp(predictions_csv)
        if preds_path: files_to_cleanup.append(preds_path)
            
        model_path = save_upload_to_temp(model_file)
        if model_path: files_to_cleanup.append(model_path)
            
        feat_path = save_upload_to_temp(feature_csv)
        if feat_path: files_to_cleanup.append(feat_path)
            
        result = run_graph_bias_pipeline(
            graph_file_path=graph_path,
            file_format=format,
            protected_attr=protected_attr,
            prediction_source=prediction_source,
            nodes_csv_path=nodes_path,
            edges_csv_path=edges_path,
            predictions_csv_path=preds_path,
            model_path=model_path,
            feature_csv_path=feat_path,
            prediction_col=prediction_col,
            ground_truth_col=ground_truth_col,
            domain=domain,
            save_audit=True
        )
        
        if result.get("status") == "error":
            return JSONResponse(status_code=400, content=result)
            
        # Add response time header
        headers = {"X-Response-Time": f"{time() - start_time:.3f}s"}
        return JSONResponse(content=result, headers=headers)
        
    except ValueError as ve:
        logger.error(f"Value error in pipeline: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error in pipeline: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
        
    finally:
        # Cleanup temporary files
        for fp in files_to_cleanup:
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                except:
                    pass
