import api from "./api";

export interface DemoAllResponse {
  dataset_audit: Record<string, unknown>;
  document_audit: Record<string, unknown>;
  model_audit: Record<string, unknown>;
  graph_audit: Record<string, unknown>;
}

export async function getDemoAll(): Promise<DemoAllResponse> {
  const { data } = await api.get<DemoAllResponse>("/api/v1/demo/all");
  return data;
}

export async function getDemoDatasetAudit() {
  const { data } = await api.get("/api/v1/demo/dataset-audit");
  return data;
}

export async function getDemoDocumentAudit() {
  const { data } = await api.get("/api/v1/demo/document-audit");
  return data;
}

export async function getDemoModelAudit() {
  const { data } = await api.get("/api/v1/demo/model-audit");
  return data;
}

export async function getDemoGraphAudit() {
  const { data } = await api.get("/api/v1/demo/graph-audit");
  return data;
}

/**
 * Fetch a demo file as a File object that can be passed to upload functions.
 */
export async function fetchDemoFile(endpoint: string, filename: string, mimeType: string): Promise<File> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  // Use native fetch for blob downloads — axios blob handling can be inconsistent
  const response = await fetch(`${baseUrl}/api/v1/demo-files/${endpoint}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch demo file: ${response.status}`);
  }
  const blob = await response.blob();
  return new File([blob], filename, { type: mimeType });
}
