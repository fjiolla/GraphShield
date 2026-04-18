import api from "./api";
import type { GraphAnalysisResult } from "@/types/graph";

export async function analyzeGraphBias(
  file: File,
  nodesFile?: File,
  config?: Record<string, unknown>
): Promise<GraphAnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  if (nodesFile) formData.append("nodes_file", nodesFile);
  if (config) formData.append("config", JSON.stringify(config));

  const { data } = await api.post<GraphAnalysisResult>(
    "/api/v1/graph/analyze-bias",
    formData,
    { headers: { "Content-Type": "multipart/form-data" }, timeout: 300000 }
  );
  return data;
}
