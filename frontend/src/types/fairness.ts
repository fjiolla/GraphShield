/* ═══════════════════════════════════════════════
   Structured audit types — /api/v1/struct-audit
   ═══════════════════════════════════════════════ */

export interface StructIngestionResult {
  table_name: string;
  row_count: number;
  column_count: number;
  columns: string[];
  format_detected: string;
  file_name: string;
  available_tables?: {
    name: string;
    row_count: number;
    column_count: number;
    columns: string[];
  }[];
}

export interface StructUploadResponse {
  status: string;
  ingestion: StructIngestionResult;
}

export interface StructRunAuditResponse {
  status: string;
  table_audited: string;
  bias_detected: boolean;
  risk_level: string;
}

export interface StructReportResponse {
  bias_detected?: boolean;
  risk_level?: string;
  [key: string]: unknown;
}

/* ═══════════════════════════════════════════════
   Struct MODEL audit — /api/v1/struct-model-audit
   ═══════════════════════════════════════════════ */

export interface FairnessScore {
  metric_name: string;
  group: string;
  score: number;
  raw_value: number;
  flagged: boolean;
}

export interface BiasVerdict {
  is_model_biased: boolean;
  bias_verdict: "BIASED" | "MARGINAL" | "FAIR";
  bias_confidence: "High" | "Medium" | "Low";
  verdict_reason: string;
  flagged_metrics_count: number;
  worst_group: string;
  worst_disparate_impact_ratio: number;
}

export interface GovernanceOutput {
  bias_scorecard: FairnessScore[];
  overall_fairness_score: number;
  audit_trail_id: string;
  remediation_plan: RemediationStep[];
  pdf_export_ready: boolean;
}

export interface RemediationStep {
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  action: string;
  description: string;
  steps: string[];
}

export interface NarrativeSection {
  title: string;
  content: string;
}

export interface ShapFeature {
  feature: string;
  importance: number;
}

export interface AutoDetectedInfo {
  sensitive_columns: string[];
  target_columns: string[];
  selected_protected_column: string;
  selected_target_column: string;
  model_type_detected: string;
  table_name: string;
  dataset_rows: number;
  dataset_columns: string[];
}

export interface StructModelAuditResponse {
  job_id: string;
  status: "completed" | "failed";
  model_format_detected: string;
  original_model_error?: string;
  protected_column: string;
  target_column: string;
  total_predictions: number;
  verdict: BiasVerdict;
  bias_metrics: Record<string, unknown>;
  shap_top_features: ShapFeature[];
  counterfactual_example: Record<string, unknown>;
  ai_narrative: NarrativeSection[];
  governance: GovernanceOutput;
  timestamp: string;
  auto_detected?: AutoDetectedInfo;
}
