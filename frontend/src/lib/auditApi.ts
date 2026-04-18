import api from "./api";
import type { AuditIngestResponse } from "@/types/audit";

export async function ingestDocument(file: File): Promise<AuditIngestResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<AuditIngestResponse>(
    "/api/v1/audit/ingest",
    formData,
    { headers: { "Content-Type": "multipart/form-data" }, timeout: 300000 }
  );
  return data;
}
