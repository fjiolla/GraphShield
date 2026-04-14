"""
struct_model_audit_schema.py
Module 2: Pydantic v2 schemas for Trained Model Bias Audit.

Defines request/response models for:
  - Model upload
  - Fairness scoring (per-group)
  - Bias verdict (BIASED / MARGINAL / FAIR)
  - Governance output (scorecard, audit trail, remediation)
  - Full audit response
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Request Schemas
# ─────────────────────────────────────────────
class StructModelUploadRequest(BaseModel):
    """
    Simplified upload — user provides only model_file + dataset_file.
    All other fields are auto-detected by the system:
      - protected_column: detected via GROQ column classification
      - target_column: detected via GROQ column classification
      - model_type: detected from file extension
      - session_id: auto-generated from dataset table name
    """
    model_type: Optional[str] = Field(None, description="Optional hint: sklearn, tensorflow, pytorch, onnx, api (auto-detected if not provided)")
    protected_column: Optional[str] = Field(None, description="Auto-detected sensitive column (override if needed)")
    target_column: Optional[str] = Field(None, description="Auto-detected target column (override if needed)")
    session_id: Optional[str] = Field(None, description="Auto-generated session ID (override if needed)")


class StructRunModelAuditRequest(BaseModel):
    """JSON body for POST /run-model-audit."""
    model_path: str = Field(..., description="Path to uploaded model file (from upload-model response)")
    session_id: str = Field(..., description="Session ID from Module 1")
    protected_column: str = Field(..., description="Protected attribute column to evaluate")
    target_column: str = Field(..., description="Target variable column")


# ─────────────────────────────────────────────
# Response Sub-Schemas
# ─────────────────────────────────────────────
class StructFairnessScore(BaseModel):
    """Per-group fairness score on a 0-100 scale."""
    metric_name: str = Field(..., description="Name of the metric (e.g. disparate_impact)")
    group: str = Field(..., description="Group label (e.g. Female, SC)")
    score: float = Field(..., description="Fairness score on 0-100 scale")
    raw_value: float = Field(..., description="Raw metric value (e.g. DIR ratio)")
    flagged: bool = Field(..., description="Whether this group is flagged for bias")


class StructBiasVerdict(BaseModel):
    """
    Top-level bias verdict — always present and first in the response.
    
    Verdict logic:
      BIASED   → any disparate_impact_ratio < 0.8 OR parity_gap > 0.2
      MARGINAL → all ratios between 0.8–0.9 AND parity_gap between 0.1–0.2
      FAIR     → all ratios >= 0.9 AND parity_gap < 0.1
    
    bias_confidence:
      High   → 2+ metrics flagged
      Medium → exactly 1 metric flagged
      Low    → 0 metrics flagged but marginal values present
    """
    is_model_biased: bool = Field(..., description="Whether the model is biased (True/False)")
    bias_verdict: str = Field(..., description="One of: BIASED / MARGINAL / FAIR")
    bias_confidence: str = Field(..., description="One of: High / Medium / Low")
    verdict_reason: str = Field(..., description="Human-readable explanation of the verdict")
    flagged_metrics_count: int = Field(..., description="Number of groups with flagged metrics")
    worst_group: str = Field(..., description="Group with the lowest disparate impact ratio")
    worst_disparate_impact_ratio: float = Field(..., description="Lowest DIR value across all groups")


class StructGovernanceOutput(BaseModel):
    """Governance layer output: scorecard, audit trail, remediation plan."""
    bias_scorecard: List[StructFairnessScore] = Field(default_factory=list, description="Per-group fairness scores")
    overall_fairness_score: float = Field(..., description="Average fairness score across all groups (0-100)")
    audit_trail_id: str = Field(..., description="Unique audit trail identifier")
    remediation_plan: List[dict] = Field(default_factory=list, description="Actionable remediation steps")
    pdf_export_ready: bool = Field(False, description="Whether PDF export is available")


class StructModelAuditResponse(BaseModel):
    """
    Full response for a model bias audit run.
    The 'verdict' field is the most critical output — always first and always populated.
    """
    job_id: str = Field(..., description="Unique job identifier for this audit run")
    status: str = Field(..., description="Audit status: completed / failed")
    model_format_detected: str = Field(..., description="Detected model format (sklearn, tensorflow, etc.)")
    protected_column: str = Field(..., description="Protected attribute column used")
    target_column: str = Field(..., description="Target variable column used")
    total_predictions: int = Field(..., description="Total number of predictions made")
    verdict: StructBiasVerdict = Field(..., description="TOP-LEVEL BIAS VERDICT — always first")
    bias_metrics: dict = Field(default_factory=dict, description="Full computed bias metrics")
    shap_top_features: List[dict] = Field(default_factory=list, description="Top SHAP feature importances")
    counterfactual_example: dict = Field(default_factory=dict, description="Counterfactual analysis result")
    ai_narrative: str = Field("", description="GROQ-generated compliance audit narrative")
    governance: StructGovernanceOutput = Field(..., description="Governance output: scorecard + remediation")
    timestamp: str = Field(..., description="ISO 8601 timestamp of audit completion")
