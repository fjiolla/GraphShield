/* ═══════════════════════════════════════════════
   Graph audit types
   ═══════════════════════════════════════════════ */

/** POST /api/v1/graph/analyze-bias response */
export interface GraphAnalysisResult {
  graph_metadata?: {
    node_count: number;
    edge_count: number;
    is_directed: boolean;
  };
  bias_metrics?: Record<string, unknown>;
  explanation?: {
    top_bias_drivers: BiasDriver[];
    summary: string;
  };
  [key: string]: unknown;
}

/* ═══════════════════════════════════════════════
   Graph MODEL audit types
   POST /api/v1/graph-model-audit/analyze
   ═══════════════════════════════════════════════ */

export interface MetricResult {
  raw_value: number | null;
  score: number | null;
  status: "PASS" | "WARN" | "FAIL" | "UNKNOWN";
  per_group?: Record<string, number>;
}

export interface PerGroupMetrics {
  count: number;
  positive_rate: number;
  accuracy: number | null;
  tpr: number | null;
  fpr: number | null;
}

export interface UniversalMetrics {
  demographic_parity: MetricResult;
  equalized_odds: MetricResult;
  disparate_impact: MetricResult;
  predictive_parity: MetricResult;
  per_group_metrics: Record<string, PerGroupMetrics>;
}

export interface StructuralMetrics {
  degree_disparity: MetricResult;
  pagerank_disparity: MetricResult;
  clustering_disparity: MetricResult;
  homophily_coefficient: MetricResult;
  prediction_centrality_correlation: MetricResult;
}

export interface BiasDriver {
  factor: string;
  description: string;
  severity: "high" | "medium" | "low";
}

export interface GlobalExplanation {
  top_bias_drivers: BiasDriver[];
  summary: string;
}

export interface GraphMetadata {
  node_count: number;
  edge_count: number;
  is_directed: boolean;
}

export interface Scorecard {
  timestamp: string;
  graph_metadata: GraphMetadata;
  protected_attribute: string;
  groups_found: string[];
  universal_metrics: UniversalMetrics;
  structural_metrics: StructuralMetrics;
  global_explanation: GlobalExplanation;
  overall_score: number;
  overall_status: "PASS" | "WARN" | "FAIL";
  key_findings: string[];
  top_risk_groups: string[];
}

export interface GeminiReport {
  summary: string;
  bias_found: string;
  likely_causes: string;
  remediation: string;
  severity_assessment: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  regulatory_note: string;
}

export interface GraphModelAuditResult {
  run_id: string;
  status: "success" | "error";
  scorecard: Scorecard;
  gemini_report: GeminiReport;
  warnings: string[];
  errors?: string[];
}

/** Saved audit trail record (from audit_logs/graph/*.json) */
export interface AuditRecord {
  run_id: string;
  timestamp: string;
  input_metadata: {
    file: string;
    format: string;
  };
  scorecard: Scorecard;
  gemini_report: GeminiReport;
  pipeline_version: string;
}

/** Audit list item (summary only) */
export interface AuditListItem {
  run_id: string;
  timestamp: string;
  format: string;
}
