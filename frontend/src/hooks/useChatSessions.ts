import { useState } from "react";
import { createChatSessionAction } from "@/actions/chat";
import type { ChatSession } from "@/types/dashboard";

export function useChatSessions(spaceId: number, initialSessions: ChatSession[]) {
  const [sessions, setSessions] = useState<ChatSession[]>(initialSessions);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(
    initialSessions.length > 0 ? initialSessions[0].id : null,
  );

  const handleCreateSession = async () => {
    try {
      const response = await createChatSessionAction(spaceId);
      setSessions((prev) => [response, ...prev]);
      setActiveSessionId(response.id);
    } catch (error) {
      console.error("Failed to create session", error);
    }
  };

  return {
    sessions,
    activeSessionId,
    setActiveSessionId,
    handleCreateSession
  };
}
