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
  const response = await api.get(`/api/v1/demo-files/${endpoint}`, {
    responseType: "blob",
  });
  const blob = new Blob([response.data], { type: mimeType });
  return new File([blob], filename, { type: mimeType });
}
