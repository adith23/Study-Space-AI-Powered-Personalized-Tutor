import { useState, useEffect } from "react";
import { listChatSessions, createChatSession } from "@/lib/api/chat";
import type { ChatSession } from "@/types/dashboard";

export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const sessionsRes = await listChatSessions();
        setSessions(sessionsRes);
        if (sessionsRes.length > 0 && !activeSessionId) {
          setActiveSessionId(sessionsRes[0].id);
        }
      } catch (error) {
        console.error("Failed to fetch sessions:", error);
      }
    };
    fetchSessions();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreateSession = async () => {
    try {
      const response = await createChatSession();
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
