import api from "./api";
import type { GraphModelAuditResult } from "@/types/graph";

export interface GraphModelAuditPayload {
  graphFile: File;
  format: "gml" | "csv" | "jsonld";
  protectedAttr: string;
  predictionSource: string;
  nodesCsv?: File;
  edgesCsv?: File;
  predictionsCsv?: File;
  modelFile?: File;
  featureCsv?: File;
  predictionCol?: string;
  groundTruthCol?: string;
  domain?: string;
}

export async function analyzeGraphModel(
  payload: GraphModelAuditPayload
): Promise<GraphModelAuditResult> {
  const formData = new FormData();
  formData.append("graph_file", payload.graphFile);
  formData.append("format", payload.format);
  formData.append("protected_attr", payload.protectedAttr || "");
  formData.append("prediction_source", payload.predictionSource);

  if (payload.nodesCsv) formData.append("nodes_csv", payload.nodesCsv);
  if (payload.edgesCsv) formData.append("edges_csv", payload.edgesCsv);
  if (payload.predictionsCsv) formData.append("predictions_csv", payload.predictionsCsv);
  if (payload.modelFile) formData.append("model_file", payload.modelFile);
  if (payload.featureCsv) formData.append("feature_csv", payload.featureCsv);
  if (payload.predictionCol && payload.predictionCol.trim() !== "") formData.append("prediction_col", payload.predictionCol.trim());
  if (payload.groundTruthCol && payload.groundTruthCol.trim() !== "") formData.append("ground_truth_col", payload.groundTruthCol.trim());
  if (payload.domain) formData.append("domain", payload.domain);

  const { data } = await api.post<GraphModelAuditResult>(
    "/api/v1/graph-model-audit/analyze",
    formData,
    { headers: { "Content-Type": "multipart/form-data" }, timeout: 360000 }
  );
  return data;
}
