"""
Serve demo files for the Try Demo feature.
Each audit page can fetch a pre-loaded demo file to run through the real pipeline.
"""

import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger("demo_files")

router = APIRouter()

# Demo files directory — adjust path relative to working directory
DEMO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "demo")

# Fallback: look in common locations
POSSIBLE_DEMO_DIRS = [
    DEMO_DIR,
    "/app/demo",  # Docker container path
    os.path.join(os.getcwd(), "demo"),
    os.path.join(os.getcwd(), "..", "demo"),
]


def _find_demo_dir() -> str:
    for d in POSSIBLE_DEMO_DIRS:
        if os.path.isdir(d):
            return d
    return DEMO_DIR


def _get_demo_file(filename: str) -> str:
    demo_dir = _find_demo_dir()
    filepath = os.path.join(demo_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Demo file not found: {filename}")
    return filepath


@router.get("/list")
async def list_demo_files():
    """List all available demo files."""
    demo_dir = _find_demo_dir()
    if not os.path.isdir(demo_dir):
        return {"files": [], "demo_dir": demo_dir, "available": False}
    
    files = os.listdir(demo_dir)
    return {
        "files": files,
        "demo_dir": demo_dir,
        "available": True,
    }


@router.get("/file/{filename}")
async def get_demo_file(filename: str):
    """Download a specific demo file."""
    filepath = _get_demo_file(filename)
    return FileResponse(filepath, filename=filename)


@router.get("/document")
async def get_demo_document():
    """Get the demo PDF document for Document Audit."""
    filepath = _get_demo_file("Hiring_Bias_Across_Indian_Cities (1).pdf")
    return FileResponse(filepath, filename="Hiring_Bias_Across_Indian_Cities.pdf", media_type="application/pdf")


@router.get("/dataset")
async def get_demo_dataset():
    """Get the demo CSV dataset for Dataset Audit."""
    filepath = _get_demo_file("adult (1).csv")
    return FileResponse(filepath, filename="adult_income.csv", media_type="text/csv")


@router.get("/model")
async def get_demo_model():
    """Get the demo pickle model for Model Audit."""
    filepath = _get_demo_file("loan_caste_biased_model (1).pkl")
    return FileResponse(filepath, filename="loan_caste_biased_model.pkl", media_type="application/octet-stream")


@router.get("/model-dataset")
async def get_demo_model_dataset():
    """Get the demo dataset that goes with the model for Model Audit."""
    filepath = _get_demo_file("loan_test_data (1).csv")
    return FileResponse(filepath, filename="loan_test_data.csv", media_type="text/csv")


@router.get("/graph")
async def get_demo_graph():
    """Get the demo GML graph for Graph Model Audit."""
    filepath = _get_demo_file("bias_high_homophily (1).gml")
    return FileResponse(filepath, filename="bias_high_homophily.gml", media_type="application/octet-stream")
