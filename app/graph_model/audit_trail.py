"""
Audit Trail module.
"""

import os
import json
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

AUDIT_DIR = os.path.join(os.getcwd(), 'audit_logs', 'graph')

def ensure_audit_dir():
    if not os.path.exists(AUDIT_DIR):
        os.makedirs(AUDIT_DIR)

def generate_run_id() -> str:
    """Generate UUID-based run ID."""
    return str(uuid.uuid4())

def save_audit_record(
    scorecard: dict,
    gemini_report: dict,
    input_metadata: dict,
    run_id: str = None
) -> str:
    """
    Save complete audit record to JSON file.
    File location: /audit_logs/graph/{run_id}.json
    Return run_id.
    """
    ensure_audit_dir()
    if not run_id:
        run_id = generate_run_id()
        
    record = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_metadata": input_metadata,
        "scorecard": scorecard,
        "gemini_report": gemini_report,
        "pipeline_version": f"1.0.0-{datetime.utcnow().strftime('%Y%m%d')}"
    }
    
    file_path = os.path.join(AUDIT_DIR, f"{run_id}.json")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        logger.info(f"Audit record saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save audit record: {e}")
        
    return run_id

def load_audit_record(run_id: str) -> dict:
    """Load a past audit record by run_id."""
    file_path = os.path.join(AUDIT_DIR, f"{run_id}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audit record {run_id} not found.")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_audit_records(limit: int = 50) -> list:
    """Return list of recent audit records (metadata only)."""
    ensure_audit_dir()
    records = []
    files = sorted([f for f in os.listdir(AUDIT_DIR) if f.endswith('.json')], reverse=True)
    for f in files[:limit]:
        try:
            with open(os.path.join(AUDIT_DIR, f), "r") as fp:
                data = json.load(fp)
                records.append({
                    "run_id": data.get("run_id"),
                    "timestamp": data.get("timestamp"),
                    "format": data.get("input_metadata", {}).get("format")
                })
        except:
            pass
    return records

if __name__ == "__main__":
    rid = save_audit_record({"score": 100}, {"text": "Good"}, {"format": "test"})
    print("Saved audit:", rid)
