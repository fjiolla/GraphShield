import api from "./api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://fjiolla-graphshield.hf.space";

export async function exportReport(auditId?: string, auditType?: string, format: string = "html"): Promise<void> {
  const params = new URLSearchParams();
  if (auditId) params.append("audit_id", auditId);
  if (auditType) params.append("audit_type", auditType);
  params.append("format", format);

  // Open the report in a new tab (HTML will render with print-to-PDF capability)
  const url = `${API_BASE}/api/v1/export/report?${params.toString()}`;
  window.open(url, "_blank");
}

export async function exportReportJSON(auditId?: string): Promise<Record<string, unknown>> {
  const params: Record<string, string> = { format: "json" };
  if (auditId) params.audit_id = auditId;
  
  const { data } = await api.get("/api/v1/export/report", { params });
  return data;
}
