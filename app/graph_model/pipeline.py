import os
import time
import logging
from app.graph_model.audit_trail import generate_run_id, save_audit_record
from app.graph_model.gml_parser import load_gml
from app.graph_model.csv_graph_parser import load_csv_graph, handle_single_csv_format
from app.graph_model.jsonld_parser import load_jsonld
from app.graph_model.graph_validator import validate_graph
from app.graph_model.prediction_resolver import resolve_predictions
from app.graph_model.universal_fairness import compute_universal_metrics
from app.graph_model.structural_fairness import compute_structural_metrics
from app.graph_model.explainability import generate_global_explanation
from app.graph_model.scorecard_builder import build_scorecard
from app.graph_model.gemini_reporter import generate_bias_report

logger = logging.getLogger(__name__)

def run_stage(stage_name: str, stage_func: callable, *args, **kwargs):
    logger.info(f"Starting stage: {stage_name}")
    start = time.time()
    try:
        res = stage_func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"Completed stage: {stage_name} in {duration:.2f}s")
        return True, res, None
    except Exception as e:
        duration = time.time() - start
        logger.error(f"Failed stage: {stage_name} in {duration:.2f}s - {e}")
        return False, None, str(e)

def detect_file_format(file_path: str) -> str:

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".gml": return "gml"
    if ext == ".csv": return "csv"
    if ext in [".json", ".jsonld"]: return "jsonld"
    raise ValueError(f"Unsupported file extension: {ext}")

def load_graph_by_format(
    file_format: str,
    graph_file_path: str,
    nodes_csv_path: str = None,
    edges_csv_path: str = None
) -> dict:
    
    if file_format == 'gml':
        return load_gml(graph_file_path)
    elif file_format == 'csv':
        actual_nodes = nodes_csv_path if nodes_csv_path else graph_file_path
        if edges_csv_path:
            return load_csv_graph(actual_nodes, edges_csv_path)
        else:
            return handle_single_csv_format(actual_nodes)
    elif file_format == 'jsonld':
        return load_jsonld(graph_file_path)
    else:
        raise ValueError(f"Unknown format: {file_format}")

def run_graph_bias_pipeline(
    graph_file_path: str,
    file_format: str,
    protected_attr: str,
    prediction_source: str,
    nodes_csv_path: str = None,
    edges_csv_path: str = None,
    predictions_csv_path: str = None,
    model_path: str = None,
    feature_csv_path: str = None,
    prediction_col: str = None,
    ground_truth_col: str = None,
    domain: str = None,
    save_audit: bool = True
) -> dict:
    """Master pipeline function. Runs all 7 stages in sequence."""
    run_id = generate_run_id()
    errors = []
    warnings = []
    
    # Stage 1: Load Graph
    succ, graph_data, err = run_stage("Load Graph", load_graph_by_format, file_format, graph_file_path, nodes_csv_path, edges_csv_path)
    if not succ:
        return {"run_id": run_id, "status": "error", "errors": [f"Load Graph: {err}"]}
        
    # Stage 2: Validate
    succ, val_res, err = run_stage("Validate Graph", validate_graph, graph_data, protected_attr)
    if succ:
        errors.extend(val_res.get("errors", []))
        warnings.extend(val_res.get("warnings", []))
        if not val_res["is_valid"]:
            return {"run_id": run_id, "status": "error", "errors": errors, "warnings": warnings}
            
    # Stage 3: Resolve Predictions
    succ, node_df, err = run_stage("Resolve Predictions", resolve_predictions, 
                                   graph_data, protected_attr, prediction_source, 
                                   predictions_csv_path, model_path, feature_csv_path, 
                                   prediction_col, ground_truth_col)
    if not succ:
        return {"run_id": run_id, "status": "error", "errors": [f"Predictions: {err}"]}
        
    # Stage 4: Fairness Metrics
    succ, u_metrics, err = run_stage("Universal Fairness", compute_universal_metrics, node_df, 'prediction', 'ground_truth', 'protected_attr')
    if not succ: u_metrics = {}
    
    succ, s_metrics, err = run_stage("Structural Fairness", compute_structural_metrics, graph_data["graph"], protected_attr, node_df)
    if not succ: s_metrics = {}
    
    # Stage 5: Explainability
    succ, global_exp, err = run_stage("Explainability", generate_global_explanation, graph_data["graph"], node_df, s_metrics, protected_attr)
    if not succ: global_exp = {}
    
    # Stage 6: Scorecard
    graph_meta = {
        "node_count": graph_data["node_count"],
        "edge_count": graph_data["edge_count"],
        "is_directed": graph_data["is_directed"]
    }
    
    # Use unique protected attribute values for groups
    groups = node_df['protected_attr'].unique() if 'protected_attr' in node_df.columns else []
    
    succ, scorecard, err = run_stage("Build Scorecard", build_scorecard, 
                                     graph_meta, u_metrics, s_metrics, global_exp, 
                                     protected_attr, groups, file_format, node_df)
                                     
    # LLM Report
    succ, report, err = run_stage("Generate Report", generate_bias_report, scorecard, domain)
    if not succ: report = {"summary": "[HARDCODED] LLM Report failed."}
    
    # Stage 7: Audit
    if save_audit:
        input_meta = {"file": graph_file_path, "format": file_format}
        save_audit_record(scorecard, report, input_meta, run_id)
        
    response = {
        "run_id": run_id,
        "status": "success",
        "scorecard": scorecard,
        "gemini_report": report,
        # "node_level_results": node_df.to_dict(orient='records')[:100],  # max 100 for safety
        "warnings": warnings
    }
    if errors:
        response["errors"] = errors
    return response

if __name__ == "__main__":
    print("Master pipeline imported.")
