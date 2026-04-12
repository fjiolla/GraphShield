
from __future__ import annotations
import json
import logging
import os
import tempfile
from typing import Any, Optional

from fastapi import APIRouter , HTTPException, File, UploadFile, Form
from pydantic import BaseModel, Field

from app.src.pipeline.orchestrator import PipelineOrchestrator, load_config
router = APIRouter()
logger = logging.getLogger(__name__)

CONFIG = load_config()
class ExplainRequest(BaseModel):
    bias_metrics: dict[str, Any] = Field(
        ..., description="Pre-computed bias metrics dict."
    )
    graph_summary: dict[str, Any] = Field(
        ..., description="Graph summary dict."
    )
    config: Optional[dict[str, Any]] = None






@router.post("/analyze-bias", tags=["Pipeline"])
async def analyze_bias(
    file: UploadFile = File(..., description="Main graph data file (or edges CSV) to analyze."),
    nodes_file: Optional[UploadFile] = File(None, description="Optional nodes CSV file (only used if main file is a CSV)."),
    config: Optional[str] = Form(None, description="Optional JSON string of config overrides merged on top of defaults.")
):
    """Run the full bias detection and explainability pipeline.

    Accepts a graph file upload, computes features, detects
    bias, generates an explanation, and returns structured results.
    """
    logger.info("POST /analyze-bias — filename=%s", file.filename)
    tmp_path = None
    nodes_tmp_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        config_overrides = None
        if config:
            config_overrides = json.loads(config)
            
        if nodes_file and nodes_file.filename:
            nodes_suffix = os.path.splitext(nodes_file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=nodes_suffix) as n_tmp:
                n_content = await nodes_file.read()
                n_tmp.write(n_content)
                nodes_tmp_path = n_tmp.name
                
            if config_overrides is None:
                config_overrides = {}
            if "graph" not in config_overrides:
                config_overrides["graph"] = {}
            config_overrides["graph"]["nodes_path"] = nodes_tmp_path

        orchestrator = PipelineOrchestrator(config=CONFIG)
        result = orchestrator.run(
            input_path=tmp_path,
            config_overrides=config_overrides,
        )
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Pipeline error")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        if nodes_tmp_path and os.path.exists(nodes_tmp_path):
            try:
                os.remove(nodes_tmp_path)
            except Exception:
                pass

