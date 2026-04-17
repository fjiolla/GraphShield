import api from "./api";
import type { StructModelAuditResponse } from "@/types/fairness";

export async function uploadAndAudit(
  modelFile: File,
  datasetFile: File
): Promise<StructModelAuditResponse> {
  const formData = new FormData();
  formData.append("model_file", modelFile);
  formData.append("dataset_file", datasetFile);

  const { data } = await api.post<StructModelAuditResponse>(
    "/api/v1/struct-model-audit/upload-and-audit",
    formData,
    { headers: { "Content-Type": "multipart/form-data" }, timeout: 180000 }
  );
  return data;
}
