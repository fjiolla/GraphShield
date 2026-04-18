"""
Prediction resolver module.
"""

import pandas as pd
import networkx as nx
import logging

logger = logging.getLogger(__name__)

def resolve_from_csv(
    predictions_csv_path: str,
    graph_data: dict,
    protected_attr: str,
    prediction_col: str,
    ground_truth_col: str = None
) -> pd.DataFrame:
    """
    Load predictions from CSV.
    Merge with graph node attributes on node_id.
    Return node_df.
    """
    from app.graph_model.gml_parser import get_node_dataframe
    node_df = get_node_dataframe(graph_data["graph"])
    
    pred_df = pd.read_csv(predictions_csv_path)
    from app.graph_model.csv_graph_parser import detect_node_id_column
    id_col = detect_node_id_column(pred_df)
    
    # Fallback auto-detect if prediction_col is not provided
    if not prediction_col:
        cands = [c for c in pred_df.columns if 'pred' in c.lower() or 'score' in c.lower() or 'label' in c.lower() or 'class' in c.lower()]
        if cands:
            prediction_col = cands[0]
        else:
            cols = [c for c in pred_df.columns if c != id_col]
            if cols:
                prediction_col = cols[-1]

    merged = pd.merge(node_df, pred_df, left_on='node_id', right_on=id_col, how='inner')
    merged['protected_attr'] = merged[protected_attr] if protected_attr in merged.columns else None
    merged['prediction'] = merged[prediction_col] if prediction_col and prediction_col in merged.columns else None
    if ground_truth_col and ground_truth_col in merged.columns:
        merged['ground_truth'] = merged[ground_truth_col]
    else:
        merged['ground_truth'] = None
        
    return merged[['node_id', 'protected_attr', 'prediction', 'ground_truth']]

def resolve_from_embedded(
    graph_data: dict,
    protected_attr: str,
    prediction_col: str,
    ground_truth_col: str = None
) -> pd.DataFrame:
    """
    Extract predictions from node attributes in graph.
    Prediction is already a column in the node DataFrame.
    """
    from app.graph_model.gml_parser import get_node_dataframe
    node_df = get_node_dataframe(graph_data["graph"])
    
    node_df['protected_attr'] = node_df[protected_attr] if protected_attr in node_df.columns else None
    
    # Fallback auto-detect if prediction_col is not provided
    if not prediction_col:
        from app.graph_model.graph_validator import check_predictions_on_nodes
        _, cands = check_predictions_on_nodes(graph_data["graph"])
        if cands:
            prediction_col = cands[0]
            
    node_df['prediction'] = node_df[prediction_col] if prediction_col in node_df.columns else None
    if ground_truth_col and ground_truth_col in node_df.columns:
        node_df['ground_truth'] = node_df[ground_truth_col]
    else:
        node_df['ground_truth'] = None
        
    return node_df[['node_id', 'protected_attr', 'prediction', 'ground_truth']]

def resolve_from_classical_model(
    model_path: str,
    feature_csv_path: str,
    graph_data: dict,
    protected_attr: str,
    ground_truth_col: str = None
) -> pd.DataFrame:
    """
    Load classical ML model + feature CSV.
    Run model.predict() on features.
    Return node_df with predictions.
    """
    from app.graph_model.gml_parser import get_node_dataframe
    node_df = get_node_dataframe(graph_data["graph"])
    node_df['protected_attr'] = node_df[protected_attr] if protected_attr in node_df.columns else None
    node_df['ground_truth'] = node_df[ground_truth_col] if ground_truth_col and ground_truth_col in node_df.columns else None
    
    # Load classical model directly so we can align input columns to training-time feature names.
    import joblib
    model = joblib.load(model_path)
    
    feat_df = pd.read_csv(feature_csv_path)
    from app.graph_model.csv_graph_parser import detect_node_id_column
    id_col = detect_node_id_column(feat_df)
    
    # Merge only the metadata columns from graph nodes to avoid duplicate feature columns
    # like age_x/age_y when node attributes overlap with feature CSV columns.
    node_meta = node_df[['node_id', 'protected_attr', 'ground_truth']]
    merged = pd.merge(node_meta, feat_df, left_on='node_id', right_on=id_col, how='inner')
    X = merged.drop(columns=[id_col, 'node_id', 'protected_attr', 'ground_truth'], errors='ignore')

    expected_features = list(getattr(model, 'feature_names_in_', []))
    if expected_features:
        missing_features = [c for c in expected_features if c not in X.columns]
        if missing_features:
            for col in missing_features:
                X[col] = 0
            logger.warning(
                "Feature CSV missing model-trained columns %s; filling with 0.",
                missing_features
            )
        X = X[expected_features]
    
    preds = model.predict(X)
    merged['prediction'] = preds
    
    return merged[['node_id', 'protected_attr', 'prediction', 'ground_truth']]

def networkx_to_pyg(G: nx.Graph) -> object:
    """
    Convert NetworkX graph to PyTorch Geometric Data object.
    Handle: node features, edge index, node labels.
    Return PyG Data object.
    Requires torch_geometric installed.
    """
    try:
        from torch_geometric.utils import from_networkx  # type: ignore[import-not-found]
        pyg_data = from_networkx(G)
        return pyg_data
    except ImportError:
        raise ImportError("torch_geometric not installed. required for PyG conversion")

def resolve_from_pytorch_model(
    model_path: str,
    graph_data: dict,
    protected_attr: str
) -> pd.DataFrame:
    """
    Load PyTorch GNN model.
    Convert NetworkX graph to PyTorch Geometric Data object.
    Run inference.
    Return node_df with predictions.
    """
    from app.graph_model.gml_parser import get_node_dataframe
    node_df = get_node_dataframe(graph_data["graph"])
    node_df['protected_attr'] = node_df[protected_attr] if protected_attr in node_df.columns else None
    node_df['ground_truth'] = None
    
    from app.graph_model.model_loader import load_model
    predict_fn = load_model(model_path)
    
    pyg_data = networkx_to_pyg(graph_data["graph"])
    preds = predict_fn(pyg_data)
    
    node_df['prediction'] = preds
    return node_df[['node_id', 'protected_attr', 'prediction', 'ground_truth']]

def resolve_predictions(
    graph_data: dict,
    protected_attr: str,
    prediction_source: str,   # 'csv', 'model', 'embedded', 'auto'
    predictions_csv_path: str = None,
    model_path: str = None,
    feature_csv_path: str = None,
    prediction_col: str = None,
    ground_truth_col: str = None
) -> pd.DataFrame:
    """
    Master resolver. Routes to correct sub-function based on source.
    """
    if prediction_source == 'auto':
        # Try embedded first
        try:
            return resolve_from_embedded(graph_data, protected_attr, prediction_col, ground_truth_col)
        except Exception:
            if predictions_csv_path:
                prediction_source = 'csv'
            elif model_path:
                prediction_source = 'model'
            else:
                raise ValueError("Could not auto-resolve predictions. Need csv or model.")
                
    if prediction_source == 'csv':
        return resolve_from_csv(predictions_csv_path, graph_data, protected_attr, prediction_col, ground_truth_col)
    elif prediction_source == 'embedded':
        return resolve_from_embedded(graph_data, protected_attr, prediction_col, ground_truth_col)
    elif prediction_source == 'model':
        from app.graph_model.model_loader import get_model_type
        m_type = get_model_type(model_path)
        if m_type == 'classical':
            return resolve_from_classical_model(model_path, feature_csv_path, graph_data, protected_attr, ground_truth_col)
        elif m_type == 'pytorch':
            return resolve_from_pytorch_model(model_path, graph_data, protected_attr)
    
    raise ValueError(f"Unknown prediction source: {prediction_source}")

if __name__ == "__main__":
    print("Smoke test prediction resolver")
