"use client";

import React, { useState, useRef, useEffect, useTransition } from "react";
import { listChatMessages, sendChatMessage } from "@/lib/api/chat";
import { Loader2 } from "lucide-react";
import ChatInputBar from "@/components/chat/ChatInputBar";
import type { UploadedFileState, ChatMessage } from "@/types/dashboard";

interface ChatInterfaceProps {
  sessionId: string;
  allFiles: UploadedFileState[];
  onFileUpload: (file: File) => Promise<void>;
  selectedFileIds: Set<number>;
  onSelectFileForContext: React.Dispatch<React.SetStateAction<Set<number>>>;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  allFiles,
  onFileUpload,
  selectedFileIds,
  onSelectFileForContext,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isPending, startTransition] = useTransition();
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const readyFiles = allFiles.filter((f) => f.status === "success");

  // Fetch message history
  useEffect(() => {
    startTransition(async () => {
      try {
        const response = await listChatMessages(sessionId);
        setMessages(response);
      } catch (error) {
        console.error("Failed to fetch chat history", error);
        setMessages([{ role: "ai", content: "Could not load chat history." }]);
      }
    });
  }, [sessionId]);

  // Scroll to bottom
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleChatSubmit = (query: string) => {
    if (!query.trim() || isPending) return;

    const userMessage: ChatMessage = { role: "human", content: query };
    setMessages((prev) => [...prev, userMessage]);

    startTransition(async () => {
      try {
        const response = await sendChatMessage(
          userMessage.content,
          sessionId,
          Array.from(selectedFileIds)
        );
        const aiMessage: ChatMessage = {
          role: "ai",
          content: response.answer,
        };
        setMessages((prev) => [...prev, aiMessage]);
      } catch (error) {
        const errorMessage: ChatMessage = {
          role: "ai",
          content: "Sorry, I encountered an error.",
        };
        setMessages((prev) => [...prev, errorMessage]);
        console.error("Chat failed", error);
      }
    });
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
        {isPending && messages[messages.length - 1]?.role === "human" && (
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
          isLoading={isPending}
          readyFiles={readyFiles}
          selectedFileIds={selectedFileIds}
          onSelectFileForContext={onSelectFileForContext}
        />
      </div>
    </div>
  );
};

export default ChatInterface;
