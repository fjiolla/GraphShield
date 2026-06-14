import api from "./api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface ChatResponse {
  reply: string;
  provider: string;
}

export async function sendChatMessage(
  message: string,
  auditContext?: string
): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/api/v1/chat/ask", {
    message,
    audit_context: auditContext || undefined,
  });
  return data;
}
