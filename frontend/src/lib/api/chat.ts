import { api } from "./client";
import type { ChatSession, ChatMessage } from "@/types/dashboard";

export async function listChatSessions() {
  const response = await api.get<ChatSession[]>("/materials/chat/sessions");
  return response.data;
}

export async function createChatSession() {
  const response = await api.post<ChatSession>("/materials/chat/sessions");
  return response.data;
}

export async function listChatMessages(sessionId: string) {
  const response = await api.get<ChatMessage[]>(`/materials/chat/sessions/${sessionId}/messages`);
  return response.data;
}

export async function sendChatMessage(query: string, sessionId: string, fileIds: number[]) {
  const response = await api.post<{ answer: string }>("/materials/chat", {
    query,
    session_id: sessionId,
    file_ids: fileIds,
  });
  return response.data;
}
