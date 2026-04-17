/* ═══════════════════════════════════════════════
   Document Audit types — POST /api/v1/audit/ingest
   ═══════════════════════════════════════════════ */

export interface BiasGroup {
  group_name: string;
  primary_keyword: string;
  bias_category: string;
  bias_type: "explicit" | "implicit";
  sentiment: "positive" | "negative" | "neutral" | "mixed";
  bias_intensity: number;
  descriptors: string[];
  evidence: string[];
  justification: string;
}

export interface BiasProfileSummary {
  overall_bias: "low" | "medium" | "high";
  dominant_bias_category: string;
  notes: string;
}

export interface DynamicProfile {
  groups: BiasGroup[];
  summary: BiasProfileSummary;
}

export interface AuditMetadata {
  document_complexity: string;
  entity_density: number;
  ner_model: string;
  llm_model: string;
  total_entities: number;
}

export interface QuantitativeVerification {
  group: string;
  contextual_proximity_score: number;
  evidence_count: number;
  mathematical_weight: "Strong" | "Moderate";
}

export interface AuditIngestResponse {
  filename: string;
  audit_metadata: {
    engine_v: string;
    status: string;
  };
  findings: {
    qualitative_analysis: {
      dynamic_profile: DynamicProfile;
      metadata: AuditMetadata;
    };
    quantitative_verification: QuantitativeVerification[];
  };
  recommendation: {
    remediation_plan: Record<string, unknown>;
  };
}
