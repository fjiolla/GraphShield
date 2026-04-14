"""
Model loader module.
"""

import os
import logging
from app.graph_model.constants import MODEL_EXTENSIONS_CLASSICAL, MODEL_EXTENSIONS_PYTORCH

logger = logging.getLogger(__name__)

def get_model_type(model_path: str) -> str:
    """
    Return 'classical', 'pytorch', or 'unknown'
    based on file extension.
    """
    _, ext = os.path.splitext(model_path)
    if ext.lower() in MODEL_EXTENSIONS_CLASSICAL:
        return 'classical'
    elif ext.lower() in MODEL_EXTENSIONS_PYTORCH:
        return 'pytorch'
    return 'unknown'

def load_classical_model(model_path: str) -> callable:
    """
    Load .pkl or .joblib model.
    Return wrapper function: predict(feature_df: pd.DataFrame) -> np.array
    """
    import joblib
    try:
        model = joblib.load(model_path)
    except Exception as e:
        logger.error(f"Failed to load classical model {model_path}: {e}")
        raise ValueError(f"Could not load classical model: {e}")
        
    def predict(feature_df):
        import numpy as np
        preds = model.predict(feature_df)
        return np.array(preds)
    return predict

def load_pytorch_model(model_path: str) -> callable:
    """
    Load .pt or .pth model.
    Try torch.load() first.
    Return wrapper: predict(graph_data) -> np.array
    If PyTorch not installed, raise ImportError with helpful message.
    """
    try:
        import torch
    except ImportError:
        raise ImportError("PyTorch not installed. Please install torch and torch_geometric to load .pt models.")
        
    try:
        # Provide weights_only=False or safe logic in production, standard map_location
        model = torch.load(model_path, map_location='cpu')
        if hasattr(model, 'eval'):
            model.eval()
    except Exception as e:
        logger.error(f"Failed to load torch model {model_path}: {e}")
        raise ValueError(f"Could not load PyTorch model: {e}")
        
    def predict(pyg_data):
        import numpy as np
        with torch.no_grad():
            preds = model(pyg_data)
        if hasattr(preds, 'numpy'):
            return preds.numpy()
        return np.array(preds)
    return predict

def load_model(model_path: str) -> callable:
    """
    Detect model format and load accordingly.
    Always returns a callable: predict(input) -> array of predictions
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
        
    m_type = get_model_type(model_path)
    if m_type == 'classical':
        return load_classical_model(model_path)
    elif m_type == 'pytorch':
        return load_pytorch_model(model_path)
    else:
        raise ValueError(f"Unsupported model format for {model_path}")

if __name__ == "__main__":
    print("Smoke test model loader...")
    # Just check imports
    import joblib
    try:
        import torch
    except ImportError:
        pass
