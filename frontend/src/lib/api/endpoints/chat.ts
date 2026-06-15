/**
 * Chat endpoints — centralized definitions.
 * Every chat-related API path is defined here ONCE.
 */

import type { Fetcher } from "../types";
import type { ChatSession, ChatMessage } from "@/types/dashboard";

export function createChatApi(fetcher: Fetcher) {
  return {
    /** POST /materials/chat/sessions — Create a new chat session */
    createSession: () =>
      fetcher<ChatSession>("/materials/chat/sessions", { method: "POST" }),

    /** GET /materials/chat/sessions — List all chat sessions */
    listSessions: () =>
      fetcher<ChatSession[]>("/materials/chat/sessions"),

    /** GET /materials/chat/sessions/{id}/messages — Get messages for a session */
    listMessages: (sessionId: string) =>
      fetcher<ChatMessage[]>(
        `/materials/chat/sessions/${sessionId}/messages`,
      ),

    /** POST /materials/chat — Send a message and get AI response */
    sendMessage: (query: string, sessionId: string, fileIds: number[]) =>
      fetcher<{ answer: string }>("/materials/chat", {
        method: "POST",
        body: JSON.stringify({
          query,
          session_id: sessionId,
          file_ids: fileIds,
        }),
      }),
  };
}
