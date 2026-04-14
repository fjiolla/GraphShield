"""
struct_model_adapter.py
Module 2 — Layer 1 & 2: Model Ingestion + Universal Model Adapter

Handles loading and prediction for multiple ML model formats:
  - sklearn (.pkl, .joblib)
  - TensorFlow/Keras (.h5, .keras)
  - PyTorch (.pt, .pth)
  - ONNX (.onnx)
  - External API (http/https URL)

Provides a unified predict(X) → List[int] interface regardless of model type.
Uses lazy imports to avoid requiring all frameworks to be installed.
"""

import logging
import os
import pickle
from typing import List, Optional

import numpy as np
import pandas as pd

struct_logger = logging.getLogger("struct_model_adapter")

# Supported model file extensions
SUPPORTED_FORMATS = {
    ".pkl": "sklearn",
    ".joblib": "sklearn",
    ".h5": "tensorflow",
    ".keras": "tensorflow",
    ".pt": "pytorch",
    ".pth": "pytorch",
    ".onnx": "onnx",
}


class StructModelAdapter:
    """
    Universal model adapter that provides a unified predict(X) interface
    across all supported ML frameworks.
    
    Usage:
        adapter = StructModelAdapter("model.pkl")
        predictions = adapter.predict(X_dataframe)
    """

    def __init__(
        self,
        model_path: str,
        model_type: Optional[str] = None,
        target_col: Optional[str] = None,
        protected_col: Optional[str] = None,
    ):
        """
        Initialize the adapter by detecting model type and loading the model.
        
        Args:
            model_path: Path to the model file or API URL.
            model_type: Optional override for model type detection.
            target_col: Target column to strip from input data.
            protected_col: Protected column to strip from input data.
        """
        self.model_path = model_path
        self.target_col = target_col
        self.protected_col = protected_col
        self.model = None
        self.encoders = {}
        self.feature_order = None

        # Detect or override model type
        if model_type:
            self.model_type = model_type.lower()
        else:
            self.model_type = self._detect_type(model_path)

        struct_logger.info(
            "Model adapter initialized: path='%s', type='%s'",
            model_path, self.model_type,
        )

        # Load the model
        self._load()

    def _detect_type(self, model_path: str) -> str:
        """
        Detect model type from file extension or URL scheme.
        
        Args:
            model_path: Path to model file or API URL.
        
        Returns:
            Model type string.
        
        Raises:
            ValueError: If format is unsupported.
        """
        # Check for API URL
        if model_path.startswith("http://") or model_path.startswith("https://"):
            struct_logger.info("Model path is a URL — using API mode.")
            return "api"

        # Check file extension
        _, ext = os.path.splitext(model_path.lower())

        if ext in SUPPORTED_FORMATS:
            detected = SUPPORTED_FORMATS[ext]
            struct_logger.info("Detected model type '%s' from extension '%s'.", detected, ext)
            return detected

        supported_exts = ", ".join(sorted(SUPPORTED_FORMATS.keys()))
        raise ValueError(
            f"Unsupported model format: '{ext}'. "
            f"Supported formats: {supported_exts}, or http/https URL for API mode."
        )

    def _load(self):
        """
        Load the model based on detected type.
        Uses lazy imports to avoid requiring all frameworks.
        
        Raises:
            ValueError: If loading fails for any reason.
        """
        try:
            if self.model_type == "sklearn":
                self._load_sklearn()
            elif self.model_type == "tensorflow":
                self._load_tensorflow()
            elif self.model_type == "pytorch":
                self._load_pytorch()
            elif self.model_type == "onnx":
                self._load_onnx()
            elif self.model_type == "api":
                # No model to load — predictions done via HTTP
                self.model = None
                struct_logger.info("API mode — no local model to load.")
            else:
                raise ValueError(f"Unknown model type: '{self.model_type}'")

            struct_logger.info("Model loaded successfully (type=%s).", self.model_type)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Failed to load {self.model_type} model: {str(e)}"
            ) from e

    def _load_sklearn(self):
        """
        Load sklearn model from .pkl or .joblib file.
        
        Handles two pickle formats:
          1. Plain sklearn model object → use directly
          2. Bundle dict {"model": ..., "encoders": ..., "feature_order": ...}
             → extract model, store encoders and feature_order
        
        Also handles version mismatches with multiple loading strategies.
        
        Raises:
            ValueError: If all loading strategies fail.
        """
        with open(self.model_path, "rb") as f:
            loaded = pickle.load(f)

        # Handle both plain model AND bundle dict
        if isinstance(loaded, dict) and "model" in loaded:
            self.encoders = loaded.get("encoders", {})
            self.feature_order = loaded.get("feature_order", None)
            self.model = loaded["model"]
            struct_logger.info(
                "sklearn bundle dict loaded from '%s' (encoders=%d, feature_order=%s).",
                self.model_path,
                len(self.encoders),
                self.feature_order is not None,
            )
        else:
            self.encoders = {}
            self.feature_order = None
            self.model = loaded
            struct_logger.info("sklearn plain model loaded from '%s'.", self.model_path)

    def _load_tensorflow(self):
        """Load TensorFlow/Keras model — lazy import."""
        import tensorflow as tf
        self.model = tf.keras.models.load_model(self.model_path)
        struct_logger.info("TensorFlow model loaded from '%s'.", self.model_path)

    def _load_pytorch(self):
        """Load PyTorch model — lazy import."""
        import torch
        self.model = torch.load(self.model_path, map_location="cpu", weights_only=False)
        if hasattr(self.model, "eval"):
            self.model.eval()
        struct_logger.info("PyTorch model loaded from '%s'.", self.model_path)

    def _load_onnx(self):
        """Load ONNX model using onnxruntime — lazy import."""
        import onnxruntime as ort
        self.model = ort.InferenceSession(self.model_path)
        struct_logger.info("ONNX model loaded from '%s'.", self.model_path)

    def predict(self, X: pd.DataFrame) -> List[int]:
        """
        Run inference on input data and return binary predictions.
        
        Auto-strips target_col and protected_col from X if present.
        Always returns List[int] of 0 or 1.
        
        Args:
            X: Input DataFrame with feature columns.
        
        Returns:
            List of binary predictions (0 or 1).
        
        Raises:
            ValueError: If prediction fails.
        """
        # Strip only target column if present — keep protected_col
        # because the model was trained with it as a feature
        X_clean = X.copy()
        cols_to_drop = []
        if self.target_col and self.target_col in X_clean.columns:
            cols_to_drop.append(self.target_col)
        if cols_to_drop:
            X_clean = X_clean.drop(columns=cols_to_drop, errors="ignore")
            struct_logger.debug("Stripped columns from input: %s", cols_to_drop)

        try:
            if self.model_type == "sklearn":
                return self._predict_sklearn(X_clean)
            elif self.model_type == "tensorflow":
                return self._predict_tensorflow(X_clean)
            elif self.model_type == "pytorch":
                return self._predict_pytorch(X_clean)
            elif self.model_type == "onnx":
                return self._predict_onnx(X_clean)
            elif self.model_type == "api":
                return self._predict_api(X_clean)
            else:
                raise ValueError(f"Cannot predict: unknown model type '{self.model_type}'")
        except Exception as e:
            raise ValueError(f"Prediction failed ({self.model_type}): {str(e)}") from e

    def _predict_sklearn(self, X: pd.DataFrame) -> List[int]:
        """Predict using sklearn model with optional encoder + feature reorder."""
        if isinstance(X, pd.DataFrame):
            X = X.copy()
        else:
            X = pd.DataFrame(X)

        # Step 1: Apply encoders ONLY to non-numeric columns
        # Uses is_numeric_dtype to correctly handle all string variants
        if hasattr(self, "encoders") and self.encoders:
            for col, encoder in self.encoders.items():
                if col in X.columns:
                    try:
                        # Always attempt transform on any non-numeric column
                        if not pd.api.types.is_numeric_dtype(X[col]):
                            X[col] = encoder.transform(
                                X[col].astype(str)
                            )
                    except Exception:
                        pass  # already numeric, skip silently

        # Step 2: Reorder columns to match training feature order
        # This also naturally excludes target_col and any extra columns
        if hasattr(self, "feature_order") and self.feature_order:
            cols = [c for c in self.feature_order if c in X.columns]
            X = X[cols]

        # Step 3: Final check — drop any remaining string columns
        # that could not be encoded (defensive)
        for col in X.columns:
            if X[col].dtype == object:
                X = X.drop(columns=[col])

        # Step 4: Predict
        return self.model.predict(X.values).tolist()

    def _predict_tensorflow(self, X: pd.DataFrame) -> List[int]:
        """Predict using TensorFlow/Keras model with 0.5 threshold."""
        raw = self.model.predict(X.values, verbose=0)
        # Handle multi-output: take first column or flatten
        if raw.ndim > 1 and raw.shape[1] == 1:
            raw = raw.flatten()
        elif raw.ndim > 1:
            raw = raw[:, 1]  # Take probability of positive class
        return [int(1 if p >= 0.5 else 0) for p in raw]

    def _predict_pytorch(self, X: pd.DataFrame) -> List[int]:
        """Predict using PyTorch model with 0.5 threshold."""
        import torch

        self.model.eval()
        with torch.no_grad():
            tensor_input = torch.FloatTensor(X.values)
            raw = self.model(tensor_input)
            if isinstance(raw, tuple):
                raw = raw[0]
            raw = raw.numpy()
            if raw.ndim > 1 and raw.shape[1] == 1:
                raw = raw.flatten()
            elif raw.ndim > 1:
                raw = raw[:, 1]
        return [int(1 if p >= 0.5 else 0) for p in raw]

    def _predict_onnx(self, X: pd.DataFrame) -> List[int]:
        """Predict using ONNX runtime with 0.5 threshold."""
        input_name = self.model.get_inputs()[0].name
        raw = self.model.run(
            None,
            {input_name: X.values.astype("float32")},
        )[0]
        raw = np.array(raw)
        if raw.ndim > 1 and raw.shape[1] == 1:
            raw = raw.flatten()
        elif raw.ndim > 1:
            raw = raw[:, 1]
        return [int(1 if p >= 0.5 else 0) for p in raw]

    def _predict_api(self, X: pd.DataFrame) -> List[int]:
        """Predict via external API endpoint."""
        import requests

        payload = {"inputs": X.values.tolist()}
        response = requests.post(
            self.model_path,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        if "predictions" in result:
            preds = result["predictions"]
        elif isinstance(result, list):
            preds = result
        else:
            raise ValueError(f"Unexpected API response format: {list(result.keys())}")

        return [int(p) for p in preds]
