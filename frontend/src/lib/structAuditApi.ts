import api from "./api";
import type {
  StructUploadResponse,
  StructRunAuditResponse,
  StructReportResponse,
} from "@/types/fairness";

export async function uploadDataset(file: File): Promise<StructUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<StructUploadResponse>(
    "/api/v1/struct-audit/upload",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}

export async function runAudit(): Promise<StructRunAuditResponse> {
  const { data } = await api.post<StructRunAuditResponse>(
    "/api/v1/struct-audit/run-audit"
  );
  return data;
}

export async function getReport(): Promise<StructReportResponse> {
  const { data } = await api.get<StructReportResponse>(
    "/api/v1/struct-audit/report"
  );
  return data;
}

export async function listTables(): Promise<{ tables: string[] }> {
  const { data } = await api.get<{ tables: string[] }>(
    "/api/v1/struct-audit/tables"
  );
  return data;
}
