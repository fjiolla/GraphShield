import api from "./api";

export interface AuditRun {
  id: string;
  type: string;
  target: string;
  date: string;
  status: string;
  score: number;
  raw_result?: unknown;
}

export async function getAudits(): Promise<AuditRun[]> {
  const { data } = await api.get<AuditRun[]>("/api/v1/system/audits");
  return data;
}
