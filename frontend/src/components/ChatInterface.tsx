import React, { useState, useRef, useEffect } from "react";
import api from "../lib/api";
import { Loader2 } from "lucide-react";
import ChatInputBar from "./ChatInputBar"; // New
import type {
  ChatMessage,
  UploadedFileState,
} from "../components/MaterialUpload";

interface ChatInterfaceProps {
  sessionId: string;
  allFiles: UploadedFileState[];
  onFileUpload: (file: File) => Promise<void>;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  allFiles,
  onFileUpload,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFileIds, setSelectedFileIds] = useState<Set<number>>(
    new Set()
  );
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const readyFiles = allFiles.filter((f) => f.status === "success");

  // Fetch message history
  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true);
      try {
        const response = await api.get<ChatMessage[]>(
          `/materials/chat/sessions/${sessionId}/messages`
        );
        setMessages(response.data);
      } catch (error) {
        console.error("Failed to fetch chat history", error);
        setMessages([{ role: "ai", content: "Could not load chat history." }]);
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory();
  }, [sessionId]);

  // Scroll to bottom
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleChatSubmit = async (query: string) => {
    if (!query.trim() || isLoading) return;

    const userMessage: ChatMessage = { role: "human", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await api.post<{ answer: string }>("/materials/chat", {
        query: userMessage.content,
        session_id: sessionId,
        file_ids: Array.from(selectedFileIds), // Can be empty
      });
      const aiMessage: ChatMessage = {
        role: "ai",
        content: response.data.answer,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: "ai",
        content: "Sorry, I encountered an error.",
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error("Chat failed", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-grow flex flex-col">
      {/* Message Display Area */}
      <div className="flex-grow overflow-y-auto space-y-4 p-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${
              msg.role === "human" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-2xl p-3 rounded-lg ${
                msg.role === "human" ? "bg-blue-600" : "bg-zinc-700"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {isLoading && messages[messages.length - 1]?.role === "human" && (
          <div className="flex justify-start">
            <div className="p-3 rounded-lg bg-zinc-700">
              <Loader2 className="animate-spin" />
            </div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 pt-2">
        <ChatInputBar
          onChatSubmit={handleChatSubmit}
          onFileUpload={onFileUpload}
          isLoading={isLoading}
          readyFiles={readyFiles}
          selectedFileIds={selectedFileIds}
          onSelectFileForContext={setSelectedFileIds}
        />
      </div>
    </div>
  );
};

export default ChatInterface;
