"""
struct_model_auditor.py
Module 2 — Layer 3 + 5: Orchestration Service

Orchestrates the full model bias audit pipeline:
  Step 1:  Retrieve Module 1 dataset from local_vault.db
  Step 2:  Validate columns against Module 1 report
  Step 3:  Load model via StructModelAdapter (with shadow fallback)
  Step 4:  Prepare data (X, groups, y_true)
  Step 5:  Run predictions
  Step 6:  Compute fairness metrics
  Step 7:  Compute bias verdict (CRITICAL)
  Step 8:  Explainability (SHAP + counterfactual)
  Step 9:  GROQ narrative
  Step 10: Governance output (scorecard, audit trail, remediation)
  Step 11: Return StructModelAuditResponse
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.core.struct_local_config import SQLITE_DB_PATH, DATA_DIR
from app.schemas.struct_model_audit_schema import (
    StructBiasVerdict,
    StructFairnessScore,
    StructGovernanceOutput,
    StructModelAuditResponse,
)
from app.services.struct_explainability import StructExplainabilityEngine
from app.services.struct_model_adapter import StructModelAdapter
from app.utils.struct_bias_metrics import (
    compute_bias_verdict,
    compute_fairness_score,
    compute_full_metrics,
)

struct_logger = logging.getLogger("struct_model_auditor")


# ─────────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────────
def _get_db_connection() -> sqlite3.Connection:
    """Open a connection to local_vault.db."""
    from pathlib import Path
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_model_audits_table(conn: sqlite3.Connection):
    """Create the model_audits table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS model_audits (
            job_id TEXT PRIMARY KEY,
            session_id TEXT,
            result_json TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()


def _ensure_audit_sessions_table(conn: sqlite3.Connection):
    """Create the audit_sessions table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_sessions (
            session_id TEXT PRIMARY KEY,
            table_name TEXT,
            report_json TEXT,
            dataset_path TEXT,
            created_at TEXT
        )
    """)
    conn.commit()


class StructModelAuditService:
    """
    Orchestrates the full model bias audit pipeline.
    
    Usage:
        service = StructModelAuditService()
        result = service.run_audit(model_path, session_id, "sex", "hired")
    """

    def run_audit(
        self,
        model_path: str,
        session_id: str,
        protected_col: str,
        target_col: str,
        model_type: Optional[str] = None,
    ) -> StructModelAuditResponse:
        """
        Execute the full 5-layer model bias audit pipeline.
        
        Args:
            model_path: Path to the uploaded model file.
            session_id: Session ID from Module 1 upload.
            protected_col: Protected attribute column to evaluate.
            target_col: Target variable column.
            model_type: Optional model type override.
        
        Returns:
            StructModelAuditResponse with full audit results.
        
        Raises:
            HTTPException: 404 if session not found, 400 if invalid column,
                          500 on audit failure.
        """
        struct_logger.info(
            "Starting model audit: session='%s', protected='%s', target='%s'",
            session_id, protected_col, target_col,
        )

        conn = _get_db_connection()
        _ensure_model_audits_table(conn)
        _ensure_audit_sessions_table(conn)

        try:
            # ── Step 1: Retrieve Module 1 dataset ──
            dataset, table_name, module1_report = self._retrieve_module1_data(
                conn, session_id
            )
            struct_logger.info(
                "Step 1 complete: Retrieved dataset '%s' (%d rows, %d cols).",
                table_name, len(dataset), len(dataset.columns),
            )

            # ── Step 2: Validate columns ──
            self._validate_columns(
                dataset, protected_col, target_col, module1_report
            )
            struct_logger.info("Step 2 complete: Columns validated.")

            # ── Step 3: Load model (with shadow fallback) ──
            adapter, model_format = self._load_model_with_fallback(
                model_path, model_type, dataset, target_col, protected_col
            )
            struct_logger.info("Step 3 complete: Model loaded (format=%s).", model_format)

            # ── Step 4: Prepare data ──
            X, groups, y_true = self._prepare_data(dataset, target_col, protected_col)
            struct_logger.info(
                "Step 4 complete: X shape=%s, groups=%d unique, y_true=%s.",
                X.shape, len(np.unique(groups)),
                "available" if y_true is not None else "N/A",
            )

            # ── Step 5: Run predictions ──
            y_pred = adapter.predict(X)
            total_predictions = len(y_pred)
            struct_logger.info(
                "Step 5 complete: %d predictions generated. "
                "Positive rate: %.2f%%",
                total_predictions,
                sum(y_pred) / len(y_pred) * 100 if y_pred else 0,
            )

            # ── Step 6: Compute metrics ──
            metrics = compute_full_metrics(y_pred, y_true, groups)
            struct_logger.info("Step 6 complete: Metrics computed.")

            # ── Step 7: Compute verdict (CRITICAL) ──
            verdict = compute_bias_verdict(
                metrics["disparate_impact"], metrics["parity_gap"]
            )
            struct_logger.info(
                "Step 7 complete: Verdict=%s, Confidence=%s, Flagged=%d",
                verdict.bias_verdict, verdict.bias_confidence,
                verdict.flagged_metrics_count,
            )

            # ── Step 8: Explainability ──
            engine = StructExplainabilityEngine()
            shap_result = engine.get_shap_values(adapter, X)
            counterfactual = engine.get_counterfactual(adapter, X)
            struct_logger.info("Step 8 complete: SHAP + counterfactual computed.")

            # ── Step 9: GROQ narrative ──
            narrative = engine.generate_groq_narrative(
                bias_report=metrics,
                shap_features=shap_result.get("feature_importances", []),
                protected_col=protected_col,
                target_col=target_col,
                verdict=verdict.model_dump(),
                module1_report=module1_report,
            )
            struct_logger.info("Step 9 complete: GROQ narrative generated.")

            # ── Step 10: Governance output ──
            governance, job_id = self._build_governance(
                metrics, verdict, conn, session_id
            )
            struct_logger.info("Step 10 complete: Governance output built.")

            # ── Step 11: Build response ──
            timestamp = datetime.now(timezone.utc).isoformat()

            response = StructModelAuditResponse(
                job_id=job_id,
                status="completed",
                model_format_detected=model_format,
                protected_column=protected_col,
                target_column=target_col,
                total_predictions=total_predictions,
                verdict=verdict,
                bias_metrics=metrics,
                shap_top_features=shap_result.get("feature_importances", []),
                counterfactual_example=counterfactual,
                ai_narrative=narrative,
                governance=governance,
                timestamp=timestamp,
            )

            # Store the result in database
            self._store_result(conn, job_id, session_id, response, timestamp)

            struct_logger.info(
                "Model audit COMPLETED: job_id='%s', verdict='%s', "
                "fairness_score=%.1f",
                job_id, verdict.bias_verdict,
                governance.overall_fairness_score,
            )

            return response

        except HTTPException:
            raise
        except Exception as e:
            struct_logger.error("Model audit FAILED: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Model audit failed: {str(e)}")
        finally:
            conn.close()

    # ─────────────────────────────────────────────
    # Step 1: Retrieve Module 1 data
    # ─────────────────────────────────────────────
    def _retrieve_module1_data(
        self, conn: sqlite3.Connection, session_id: str
    ) -> tuple:
        """
        Retrieve dataset and report from Module 1 using session_id.
        
        Strategy:
          1. Try audit_sessions table first (formal session storage)
          2. If not found, try using session_id as a table name directly
             (Module 1 stores datasets as named SQLite tables)
        
        Returns:
            Tuple of (dataset_df, table_name, module1_report_dict_or_None)
        """
        # Strategy 1: Try audit_sessions table
        try:
            cursor = conn.execute(
                "SELECT table_name, report_json, dataset_path "
                "FROM audit_sessions WHERE session_id = ?",
                (session_id,),
            )
            row = cursor.fetchone()

            if row:
                table_name = row[0] if row[0] else session_id
                report_json = row[1]
                dataset_path = row[2]

                module1_report = None
                if report_json:
                    try:
                        module1_report = json.loads(report_json)
                    except json.JSONDecodeError:
                        struct_logger.warning("Could not parse Module 1 report JSON.")

                # Load dataset from the table
                dataset = pd.read_sql_query(
                    f'SELECT * FROM "{table_name}"', conn
                )
                if not dataset.empty:
                    return dataset, table_name, module1_report
        except Exception as e:
            struct_logger.debug("audit_sessions lookup failed: %s", e)

        # Strategy 2: Use session_id as table name directly
        # (Module 1 stores datasets as SQLite tables named after the file)
        try:
            # Check if a table matching session_id exists
            tables_cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            all_tables = [r[0] for r in tables_cursor.fetchall()]
            
            # Filter out system tables
            data_tables = [
                t for t in all_tables
                if t not in ("model_audits", "audit_sessions", "sqlite_sequence")
            ]

            # Try exact match
            if session_id in data_tables:
                dataset = pd.read_sql_query(
                    f'SELECT * FROM "{session_id}"', conn
                )
                if not dataset.empty:
                    struct_logger.info(
                        "Found dataset as table '%s' (%d rows).",
                        session_id, len(dataset),
                    )
                    return dataset, session_id, None

            # Try case-insensitive match
            for t in data_tables:
                if t.lower() == session_id.lower():
                    dataset = pd.read_sql_query(f'SELECT * FROM "{t}"', conn)
                    if not dataset.empty:
                        struct_logger.info(
                            "Found dataset as table '%s' (case-insensitive match).",
                            t,
                        )
                        return dataset, t, None

            # If only one data table exists, use it as fallback
            if len(data_tables) == 1:
                table_name = data_tables[0]
                dataset = pd.read_sql_query(
                    f'SELECT * FROM "{table_name}"', conn
                )
                if not dataset.empty:
                    struct_logger.info(
                        "Using only available data table '%s' as fallback.",
                        table_name,
                    )
                    return dataset, table_name, None

            # List available tables for error message
            table_info = []
            for t in data_tables:
                try:
                    count = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                    table_info.append(f"'{t}' ({count} rows)")
                except Exception:
                    table_info.append(f"'{t}'")

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Session '{session_id}' not found. "
                    f"Run Module 1 upload first. "
                    f"Available tables: {', '.join(table_info) if table_info else 'none'}"
                ),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found. Run Module 1 upload first. Error: {str(e)}",
            )

    # ─────────────────────────────────────────────
    # Step 2: Validate columns
    # ─────────────────────────────────────────────
    def _validate_columns(
        self,
        dataset: pd.DataFrame,
        protected_col: str,
        target_col: str,
        module1_report: Optional[dict],
    ):
        """Validate that protected and target columns exist in the dataset."""
        # Check against Module 1 report if available
        if module1_report:
            ds_overview = module1_report.get("dataset_overview", {})
            sensitive_columns = ds_overview.get("sensitive_columns", [])
            target_columns = ds_overview.get("target_columns", [])

            if sensitive_columns and protected_col not in sensitive_columns:
                struct_logger.warning(
                    "Column '%s' not in Module 1 sensitive columns %s. "
                    "Checking dataset directly.",
                    protected_col, sensitive_columns,
                )
            if target_columns and target_col not in target_columns:
                struct_logger.warning(
                    "Column '%s' not in Module 1 target columns %s. "
                    "Checking dataset directly.",
                    target_col, target_columns,
                )

        # Always validate against actual dataset columns
        if protected_col not in dataset.columns:
            available = list(dataset.columns)
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Protected column '{protected_col}' not found in dataset. "
                    f"Available columns: {available}"
                ),
            )

        if target_col not in dataset.columns:
            available = list(dataset.columns)
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Target column '{target_col}' not found in dataset. "
                    f"Available columns: {available}"
                ),
            )

    # ─────────────────────────────────────────────
    # Step 3: Load model with shadow fallback
    # ─────────────────────────────────────────────
    def _load_model_with_fallback(
        self,
        model_path: str,
        model_type: Optional[str],
        dataset: pd.DataFrame,
        target_col: str,
        protected_col: str,
    ) -> tuple:
        """
        Load the model and run a smoke test.
        If the model fails, fall back to a shadow LogisticRegression.
        
        Returns:
            Tuple of (adapter, model_format_detected_str)
        """
        try:
            adapter = StructModelAdapter(
                model_path,
                model_type=model_type,
                target_col=target_col,
                protected_col=protected_col,
            )

            # Smoke test with 3 rows
            test_X = dataset.head(3).drop(
                columns=[target_col, protected_col], errors="ignore"
            )
            smoke_preds = adapter.predict(test_X)
            struct_logger.info(
                "Model smoke test passed: %d predictions from %d rows.",
                len(smoke_preds), len(test_X),
            )
            return adapter, adapter.model_type

        except Exception as e:
            struct_logger.warning(
                "Original model failed: %s. Falling back to shadow model.", str(e)
            )
            return self._train_shadow_model(
                dataset, target_col, protected_col, str(e)
            )

    def _train_shadow_model(
        self,
        dataset: pd.DataFrame,
        target_col: str,
        protected_col: str,
        original_error: str,
    ) -> tuple:
        """Train a LogisticRegression shadow model as fallback."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import LabelEncoder

        struct_logger.info("Training shadow LogisticRegression model...")

        X = dataset.drop(columns=[target_col, protected_col], errors="ignore")
        y = dataset[target_col]

        # Encode categorical columns
        label_encoders = {}
        for col in X.select_dtypes(include=["object", "category"]).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le

        # Encode target if needed
        if y.dtype == "object":
            le_target = LabelEncoder()
            y = le_target.fit_transform(y)

        # Handle NaN values
        X = X.fillna(0)

        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X.values, y)

        # Create a mock adapter
        adapter = StructModelAdapter.__new__(StructModelAdapter)
        adapter.model = model
        adapter.model_type = "sklearn"
        adapter.model_path = "shadow_model"
        adapter.target_col = target_col
        adapter.protected_col = protected_col

        model_format = (
            f"shadow_logistic_regression "
            f"(original model failed: {original_error})"
        )

        struct_logger.info("Shadow model trained successfully.")
        print(
            f"⚠️  WARNING: Using shadow LogisticRegression model. "
            f"Original model failed: {original_error}"
        )

        return adapter, model_format

    # ─────────────────────────────────────────────
    # Step 4: Prepare data
    # ─────────────────────────────────────────────
    def _prepare_data(
        self,
        dataset: pd.DataFrame,
        target_col: str,
        protected_col: str,
    ) -> tuple:
        """
        Prepare X, groups, and y_true from the dataset.
        Handles encoding of categorical features.
        """
        from sklearn.preprocessing import LabelEncoder

        groups = dataset[protected_col].values
        y_true = dataset[target_col].values

        # Convert target to numeric if needed
        if y_true.dtype == object:
            le = LabelEncoder()
            y_true = le.fit_transform(y_true.astype(str))

        X = dataset.drop(columns=[target_col, protected_col], errors="ignore")

        # Encode categorical features for prediction
        for col in X.select_dtypes(include=["object", "category"]).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))

        # Handle NaN values
        X = X.fillna(0)

        return X, groups, y_true

    # ─────────────────────────────────────────────
    # Step 10: Build governance output
    # ─────────────────────────────────────────────
    def _build_governance(
        self,
        metrics: dict,
        verdict: StructBiasVerdict,
        conn: sqlite3.Connection,
        session_id: str,
    ) -> tuple:
        """
        Build governance output: scorecard, audit trail, remediation plan.
        
        Returns:
            Tuple of (StructGovernanceOutput, job_id)
        """
        di_data = metrics.get("disparate_impact", {})
        groups_data = di_data.get("groups", {})

        # Build per-group fairness scores
        fairness_scores = []
        for group, data in groups_data.items():
            ratio = data.get("disparate_impact_ratio", 0)
            score = compute_fairness_score(ratio, "disparate_impact")
            fairness_scores.append(
                StructFairnessScore(
                    metric_name="disparate_impact",
                    group=str(group),
                    score=score,
                    raw_value=round(float(ratio), 6),
                    flagged=data.get("flagged", False),
                )
            )

        # Overall fairness score = average of all group scores
        if fairness_scores:
            overall_score = round(
                sum(fs.score for fs in fairness_scores) / len(fairness_scores),
                2,
            )
        else:
            overall_score = 0.0

        # Generate audit trail ID
        job_id = str(uuid4())
        audit_trail_id = f"{job_id}_{datetime.now(timezone.utc).isoformat()}"

        # Remediation plan based on verdict
        remediation_plan = self._generate_remediation_plan(verdict, metrics)

        governance = StructGovernanceOutput(
            bias_scorecard=fairness_scores,
            overall_fairness_score=overall_score,
            audit_trail_id=audit_trail_id,
            remediation_plan=remediation_plan,
            pdf_export_ready=False,
        )

        return governance, job_id

    def _generate_remediation_plan(
        self, verdict: StructBiasVerdict, metrics: dict
    ) -> list:
        """Generate remediation steps based on the verdict."""
        plan = []

        if verdict.bias_verdict == "BIASED":
            plan.extend([
                {
                    "priority": "HIGH",
                    "action": "Immediate Model Review Required",
                    "description": (
                        f"The model shows significant bias against '{verdict.worst_group}' "
                        f"with a disparate impact ratio of {verdict.worst_disparate_impact_ratio}. "
                        f"The 80% rule threshold is violated."
                    ),
                    "steps": [
                        "Audit training data for representation imbalance",
                        "Apply reweighting or resampling techniques",
                        "Consider adversarial debiasing during model training",
                    ],
                },
                {
                    "priority": "HIGH",
                    "action": "Feature Engineering Review",
                    "description": (
                        "Review features for proxy discrimination. "
                        "Features correlated with protected attributes may "
                        "perpetuate historical biases."
                    ),
                    "steps": [
                        "Run correlation analysis between features and protected attribute",
                        "Remove or transform highly correlated proxy features",
                        "Test model performance after feature modification",
                    ],
                },
                {
                    "priority": "MEDIUM",
                    "action": "Implement Continuous Monitoring",
                    "description": (
                        "Deploy fairness metrics monitoring in production "
                        "to detect drift in bias over time."
                    ),
                    "steps": [
                        "Set up disparate impact ratio alerts (threshold < 0.8)",
                        "Monitor prediction distributions by group weekly",
                        "Establish a bias review board for quarterly audits",
                    ],
                },
            ])
        elif verdict.bias_verdict == "MARGINAL":
            plan.extend([
                {
                    "priority": "MEDIUM",
                    "action": "Proactive Bias Mitigation",
                    "description": (
                        "The model is approaching bias thresholds. "
                        "Preventive action recommended."
                    ),
                    "steps": [
                        "Monitor disparate impact ratios closely",
                        "Consider calibration techniques",
                        "Review training data balance quarterly",
                    ],
                },
            ])
        else:
            plan.append({
                "priority": "LOW",
                "action": "Maintain Current Standards",
                "description": (
                    "Model meets fairness criteria. Continue regular monitoring."
                ),
                "steps": [
                    "Schedule annual bias audits",
                    "Monitor for data drift",
                ],
            })

        return plan

    # ─────────────────────────────────────────────
    # Store result in database
    # ─────────────────────────────────────────────
    def _store_result(
        self,
        conn: sqlite3.Connection,
        job_id: str,
        session_id: str,
        response: StructModelAuditResponse,
        timestamp: str,
    ):
        """Store the audit result in local_vault.db for later retrieval."""
        try:
            # Use json.dumps with custom handler for numpy types
            def _default_serializer(obj):
                if isinstance(obj, (np.bool_,)):
                    return bool(obj)
                if isinstance(obj, (np.integer,)):
                    return int(obj)
                if isinstance(obj, (np.floating,)):
                    return float(obj)
                if isinstance(obj, (np.str_,)):
                    return str(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                return str(obj)

            result_dict = response.model_dump()
            result_json = json.dumps(result_dict, default=_default_serializer)
            conn.execute(
                "INSERT INTO model_audits (job_id, session_id, result_json, timestamp) "
                "VALUES (?, ?, ?, ?)",
                (job_id, session_id, result_json, timestamp),
            )
            conn.commit()
            struct_logger.info("Audit result stored: job_id='%s'", job_id)
        except Exception as e:
            struct_logger.error("Failed to store audit result: %s", str(e))
