"""
struct_explainability.py
Module 2 — Layer 4: Explainability Engine

Provides three explainability outputs:
  1. SHAP values — black-box feature importance via shap.Explainer
  2. Counterfactuals — flip features ±10% to find decision boundary
  3. GROQ AI narrative — compliance audit report via Llama 3 70B

Uses GROQ API (NOT OpenAI, NOT Claude, NOT Gemini) for narrative generation.
"""

import json
import logging
import os
from typing import List, Optional

import numpy as np
import pandas as pd
import requests

struct_logger = logging.getLogger("struct_explainability")


class StructExplainabilityEngine:
    """
    Explainability engine for model bias audits.
    
    Provides SHAP-based feature importance, counterfactual analysis,
    and GROQ LLM-powered narrative generation.
    """

    def __init__(self):
        struct_logger.info("Explainability engine initialized.")

    # ─────────────────────────────────────────────
    # SHAP Feature Importance
    # ─────────────────────────────────────────────
    def get_shap_values(
        self,
        adapter,
        X: pd.DataFrame,
    ) -> dict:
        """
        Compute SHAP values using a model-agnostic (black-box) explainer.
        
        Uses shap.Explainer with the adapter's predict function, which works
        on any model regardless of framework.
        
        Args:
            adapter: StructModelAdapter instance with a predict(X) method.
            X: Feature DataFrame (already cleaned of target/protected columns).
        
        Returns:
            Dict with 'feature_importances' (top 5 features by mean |SHAP|).
            On failure: returns empty list with error message.
        """
        try:
            import shap

            struct_logger.info("Computing SHAP values for %d samples, %d features...", len(X), len(X.columns))

            # Use a subsample for background (SHAP can be slow on large datasets)
            background_size = min(50, len(X))
            background = X.sample(n=background_size, random_state=42)

            # Black-box explainer — works on any model type
            def predict_fn(data):
                if isinstance(data, np.ndarray):
                    data = pd.DataFrame(data, columns=X.columns)
                return np.array(adapter.predict(data))

            explainer = shap.Explainer(predict_fn, background)

            # Compute SHAP values (limit to 100 samples for performance)
            sample_size = min(100, len(X))
            X_sample = X.head(sample_size)
            shap_values = explainer(X_sample)

            # Extract mean absolute SHAP values per feature
            if hasattr(shap_values, "values"):
                vals = np.abs(shap_values.values)
            else:
                vals = np.abs(np.array(shap_values))

            mean_shap = vals.mean(axis=0)

            feature_importance = []
            for i, col in enumerate(X.columns[:len(mean_shap)]):
                feature_importance.append({
                    "feature": str(col),
                    "mean_shap": round(float(mean_shap[i]), 6),
                })

            # Sort by mean SHAP descending, take top 5
            feature_importance.sort(key=lambda x: x["mean_shap"], reverse=True)
            top_features = feature_importance[:5]

            struct_logger.info(
                "SHAP computation complete. Top feature: '%s' (%.4f)",
                top_features[0]["feature"] if top_features else "N/A",
                top_features[0]["mean_shap"] if top_features else 0,
            )

            return {"feature_importances": top_features}

        except Exception as e:
            struct_logger.error("SHAP computation failed: %s", str(e))
            return {
                "feature_importances": [],
                "error": f"SHAP unavailable: {str(e)}",
            }

    # ─────────────────────────────────────────────
    # Counterfactual Analysis
    # ─────────────────────────────────────────────
    def get_counterfactual(
        self,
        adapter,
        X: pd.DataFrame,
        row_index: int = 0,
    ) -> dict:
        """
        Generate a counterfactual example by flipping numeric features ±10%.
        
        Takes one row, iteratively perturbs numeric features until the
        prediction flips, up to 20 iterations.
        
        Args:
            adapter: StructModelAdapter instance.
            X: Feature DataFrame.
            row_index: Index of the row to generate counterfactual for.
        
        Returns:
            Dict with original/modified row, changed features, and predictions.
            If not found: returns message indicating no counterfactual within threshold.
        """
        try:
            if row_index >= len(X):
                row_index = 0

            original_row = X.iloc[row_index].copy()
            original_pred = adapter.predict(pd.DataFrame([original_row]))[0]

            struct_logger.info(
                "Generating counterfactual for row %d (original prediction: %d)...",
                row_index, original_pred,
            )

            numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                return {"message": "No numeric features available for counterfactual analysis"}

            modified_row = original_row.copy()
            changed_features = []

            for iteration in range(20):
                # Perturb a random numeric feature by ±10%
                col = numeric_cols[iteration % len(numeric_cols)]
                current_val = modified_row[col]

                if current_val == 0:
                    # If value is 0, add a small perturbation
                    perturbation = np.random.choice([-0.1, 0.1])
                else:
                    perturbation = current_val * np.random.choice([-0.1, 0.1])

                modified_row[col] = current_val + perturbation

                if col not in changed_features:
                    changed_features.append(col)

                # Check if prediction flipped
                new_pred = adapter.predict(pd.DataFrame([modified_row]))[0]

                if new_pred != original_pred:
                    struct_logger.info(
                        "Counterfactual found after %d iterations. "
                        "Prediction flipped from %d to %d. Changed: %s",
                        iteration + 1, original_pred, new_pred, changed_features,
                    )
                    return {
                        "original_row": {k: _safe_value(v) for k, v in original_row.to_dict().items()},
                        "modified_row": {k: _safe_value(v) for k, v in modified_row.to_dict().items()},
                        "changed_features": changed_features,
                        "original_prediction": int(original_pred),
                        "counterfactual_prediction": int(new_pred),
                        "iterations": iteration + 1,
                    }

            struct_logger.info("No counterfactual found within 20 iterations.")
            return {"message": "No counterfactual found within threshold"}

        except Exception as e:
            struct_logger.error("Counterfactual generation failed: %s", str(e))
            return {"message": f"Counterfactual analysis failed: {str(e)}"}

    # ─────────────────────────────────────────────
    # GROQ AI Narrative Generation
    # ─────────────────────────────────────────────
    def generate_groq_narrative(
        self,
        bias_report: dict,
        shap_features: list,
        protected_col: str,
        target_col: str,
        verdict: dict,
        module1_report: Optional[dict] = None,
    ) -> str:
        """
        Generate an AI compliance audit narrative using GROQ API (Llama 3 70B).
        
        Produces a structured 5-section report:
          1. VERDICT — restated bias determination
          2. IMPACT — most disadvantaged group and magnitude
          3. ROOT CAUSE — top 2 SHAP features causing bias
          4. DATA vs MODEL — comparison with Module 1 data bias
          5. REMEDIATION — two actionable steps
        
        Includes 3 retries with exponential backoff for transient network failures.
        Falls back to a locally-generated narrative if the API is unreachable.
        
        Args:
            bias_report: Full computed bias metrics dict.
            shap_features: Top SHAP feature importances list.
            protected_col: Protected attribute column name.
            target_col: Target variable column name.
            verdict: Bias verdict dict.
            module1_report: Optional Module 1 report for cross-referencing.
        
        Returns:
            String narrative (max ~250 words).
            On failure: returns locally-generated fallback narrative.
        """
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            struct_logger.warning("GROQ_API_KEY not set — generating local fallback narrative.")
            return self._generate_local_narrative(
                bias_report, shap_features, protected_col, target_col, verdict, module1_report
            )

        try:
            # Build Module 1 summary if available
            module1_summary = "Not available"
            if module1_report:
                m1_bias = module1_report.get("bias_detected", "Unknown")
                m1_risk = module1_report.get("risk_level", "Unknown")
                m1_sensitive = module1_report.get("dataset_overview", {}).get("sensitive_columns", [])
                module1_summary = (
                    f"Data bias detected: {m1_bias}, Risk level: {m1_risk}, "
                    f"Sensitive columns: {m1_sensitive}"
                )

            # Serialize inputs for prompt
            bias_metrics_str = json.dumps(bias_report, default=str, indent=None)[:1500]
            shap_str = json.dumps(shap_features, default=str)[:500]

            user_content = (
                f"A trained ML model has been audited. Here are findings:\n\n"
                f"BIAS VERDICT: {verdict.get('bias_verdict', 'Unknown')}\n"
                f"CONFIDENCE: {verdict.get('bias_confidence', 'Unknown')}\n"
                f"REASON: {verdict.get('verdict_reason', 'N/A')}\n\n"
                f"Bias Metrics: {bias_metrics_str}\n"
                f"Top SHAP Features: {shap_str}\n"
                f"Protected Attribute: {protected_col}\n"
                f"Target Variable: {target_col}\n"
                f"Pre-model data bias from Part 1: {module1_summary}\n\n"
                f"Write a compliance audit report (max 250 words) with exactly "
                f"5 sections:\n"
                f"1. VERDICT: Restate clearly — is this model BIASED, MARGINAL, or FAIR?\n"
                f"2. IMPACT: Which group is most disadvantaged and by what magnitude?\n"
                f"3. ROOT CAUSE: Top 2 SHAP features causing bias with values\n"
                f"4. DATA vs MODEL: Does model bias match the data bias from Part 1?\n"
                f"5. REMEDIATION: Two specific actionable steps to reduce bias\n\n"
                f"Use plain English. No data science jargon."
            )

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an AI ethics compliance officer. Write bias "
                            "audit reports that are direct, legally-grounded, "
                            "and actionable. Always lead with the bias verdict."
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_content,
                    },
                ],
                "max_tokens": 600,
                "temperature": 0.3,
            }

            # Retry with exponential backoff (3 attempts)
            import time
            max_retries = 3
            last_error = None

            for attempt in range(1, max_retries + 1):
                try:
                    struct_logger.info(
                        "GROQ API attempt %d/%d...", attempt, max_retries
                    )
                    response = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {groq_api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                        timeout=30,
                    )
                    response.raise_for_status()

                    result = response.json()
                    narrative = result["choices"][0]["message"]["content"]

                    struct_logger.info(
                        "GROQ narrative generated successfully on attempt %d (%d chars).",
                        attempt, len(narrative),
                    )
                    return narrative

                except (requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout,
                        requests.exceptions.DNSError if hasattr(requests.exceptions, 'DNSError') else ConnectionError) as e:
                    last_error = e
                    if attempt < max_retries:
                        wait_time = 2 ** attempt  # 2s, 4s
                        struct_logger.warning(
                            "GROQ API attempt %d failed (network): %s. "
                            "Retrying in %ds...",
                            attempt, str(e)[:100], wait_time,
                        )
                        time.sleep(wait_time)
                    else:
                        struct_logger.error(
                            "GROQ API failed after %d attempts: %s",
                            max_retries, str(e)[:200],
                        )

                except Exception as e:
                    last_error = e
                    struct_logger.error(
                        "GROQ API non-retryable error on attempt %d: %s",
                        attempt, str(e),
                    )
                    break  # Don't retry on non-network errors (e.g., 401, 400)

            # All retries failed — generate local fallback
            struct_logger.warning(
                "GROQ API unreachable after %d attempts. "
                "Generating local fallback narrative.",
                max_retries,
            )
            return self._generate_local_narrative(
                bias_report, shap_features, protected_col, target_col,
                verdict, module1_report
            )

        except Exception as e:
            struct_logger.error("GROQ narrative generation failed: %s", str(e))
            return self._generate_local_narrative(
                bias_report, shap_features, protected_col, target_col,
                verdict, module1_report
            )

    def _generate_local_narrative(
        self,
        bias_report: dict,
        shap_features: list,
        protected_col: str,
        target_col: str,
        verdict: dict,
        module1_report: Optional[dict] = None,
    ) -> str:
        """
        Generate a structured compliance narrative locally when GROQ API
        is unavailable. Produces the same 5-section report format.
        
        Args:
            bias_report: Full computed bias metrics dict.
            shap_features: Top SHAP feature importances list.
            protected_col: Protected attribute column name.
            target_col: Target variable column name.
            verdict: Bias verdict dict.
            module1_report: Optional Module 1 report for cross-referencing.
        
        Returns:
            String narrative with 5 structured sections.
        """
        bias_verdict = verdict.get("bias_verdict", "Unknown")
        confidence = verdict.get("bias_confidence", "Unknown")
        reason = verdict.get("verdict_reason", "N/A")
        worst_group = verdict.get("worst_group", "Unknown")
        worst_dir = verdict.get("worst_disparate_impact_ratio", "N/A")

        # Extract disparate impact details
        di_data = bias_report.get("disparate_impact", {})
        privileged_group = di_data.get("privileged_group", "Unknown")
        parity_gap = bias_report.get("parity_gap", 0)

        # Top SHAP features
        top_2_features = shap_features[:2] if shap_features else []
        shap_summary = ", ".join(
            [f"'{f['feature']}' (importance: {f['mean_shap']:.4f})" for f in top_2_features]
        ) if top_2_features else "No SHAP features available"

        # Module 1 comparison
        if module1_report:
            m1_bias = module1_report.get("bias_detected", "Unknown")
            m1_risk = module1_report.get("risk_level", "Unknown")
            data_vs_model = (
                f"Module 1 detected data bias: {m1_bias} (risk: {m1_risk}). "
                f"The model's {bias_verdict.lower()} verdict suggests that "
                f"{'the model may be amplifying pre-existing data biases' if bias_verdict == 'BIASED' else 'the model handles the data biases reasonably'}."
            )
        else:
            data_vs_model = (
                "Module 1 data bias report is not available for comparison. "
                "It is recommended to run Module 1 first to understand whether "
                "model bias originates from the training data or the model itself."
            )

        # Build narrative
        sections = []

        # Section 1: VERDICT
        sections.append(
            f"1. VERDICT: This model is {bias_verdict} with {confidence} confidence. {reason}"
        )

        # Section 2: IMPACT
        if bias_verdict == "BIASED":
            sections.append(
                f"2. IMPACT: The group '{worst_group}' is most disadvantaged with a "
                f"disparate impact ratio of {worst_dir} compared to the privileged "
                f"group '{privileged_group}'. The parity gap of {parity_gap:.4f} indicates "
                f"a significant disparity in positive outcome rates between groups."
            )
        elif bias_verdict == "MARGINAL":
            sections.append(
                f"2. IMPACT: The group '{worst_group}' shows marginally lower "
                f"outcomes with a disparate impact ratio of {worst_dir}. "
                f"While not violating the 80% rule, the disparity warrants monitoring."
            )
        else:
            sections.append(
                f"2. IMPACT: No significant disadvantaged group identified. "
                f"All groups show comparable outcome rates with a parity gap of {parity_gap:.4f}."
            )

        # Section 3: ROOT CAUSE
        sections.append(
            f"3. ROOT CAUSE: The top features driving model decisions are: {shap_summary}. "
            f"These features should be reviewed for potential proxy discrimination "
            f"with the protected attribute '{protected_col}'."
        )

        # Section 4: DATA vs MODEL
        sections.append(f"4. DATA vs MODEL: {data_vs_model}")

        # Section 5: REMEDIATION
        if bias_verdict == "BIASED":
            sections.append(
                f"5. REMEDIATION: (a) Audit the training data for representation "
                f"imbalance in the '{protected_col}' attribute and apply reweighting "
                f"or resampling techniques to balance group representation. "
                f"(b) Review and potentially remove features that serve as proxies "
                f"for '{protected_col}', particularly the top SHAP features that "
                f"may encode protected characteristics indirectly."
            )
        elif bias_verdict == "MARGINAL":
            sections.append(
                f"5. REMEDIATION: (a) Implement continuous monitoring of disparate "
                f"impact ratios with alerts when they drop below 0.8. "
                f"(b) Consider calibration techniques to ensure prediction "
                f"probabilities are well-calibrated across groups."
            )
        else:
            sections.append(
                f"5. REMEDIATION: (a) Schedule regular annual bias audits to "
                f"ensure fairness metrics remain within acceptable bounds. "
                f"(b) Monitor for data drift that could introduce bias over time."
            )

        narrative = "\n\n".join(sections)
        struct_logger.info(
            "Local fallback narrative generated (%d chars).", len(narrative)
        )
        return narrative


def _safe_value(v):
    """Convert numpy/pandas types to JSON-serializable Python types."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.ndarray,)):
        return v.tolist()
    if pd.isna(v):
        return None
    return v

