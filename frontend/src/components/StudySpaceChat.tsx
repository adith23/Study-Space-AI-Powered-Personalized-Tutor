"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import Sidebar from "@/components/Sidebar"; // New
import ChatInterface from "@/components/ChatInterface"; // Updated
import FlashcardWorkspace from "@/components/FlashcardWorkspace";
import QuizWorkspace from "@/components/QuizWorkspace";

export interface UploadedFileState {
  id: number;
  name: string;
  status: "pending" | "processing" | "success" | "failed";
}

interface UploadedFileUploadResponse {
  id: number;
  name: string;
  status?: UploadedFileState["status"];
}

interface UploadedFileListResponse {
  id: number;
  name: string | null;
  status: string;
}
export interface ChatSession {
  id: string;
  name: string;
}
export interface ChatMessage {
  role: "human" | "ai";
  content: string;
}

type WorkspaceView = "chat" | "quiz" | "flashcards";

const VALID_FILE_STATUSES = new Set<UploadedFileState["status"]>([
  "pending",
  "processing",
  "success",
  "failed",
]);

function normalizeFileStatus(status: string | undefined): UploadedFileState["status"] {
  if (status && VALID_FILE_STATUSES.has(status as UploadedFileState["status"])) {
    return status as UploadedFileState["status"];
  }
  return "pending";
}

function normalizeUploadedFile(
  file: UploadedFileListResponse | UploadedFileUploadResponse
): UploadedFileState {
  return {
    id: file.id,
    name: file.name ?? "Untitled document",
    status: normalizeFileStatus(file.status),
  };
}

// --- MAIN PAGE COMPONENT ---
export default function StudySpaceChat() {
  const [files, setFiles] = useState<UploadedFileState[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [selectedFileIds, setSelectedFileIds] = useState<Set<number>>(new Set());
  const [activeView, setActiveView] = useState<WorkspaceView>("chat");

  // Effect for fetching initial sessions
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await api.get<ChatSession[]>(
          "/materials/chat/sessions"
        );
        setSessions(response.data);
        if (response.data.length > 0 && !activeSessionId) {
          setActiveSessionId(response.data[0].id);
        }
      } catch (error) {
        console.error("Failed to fetch chat sessions:", error);
      }
    };

    const fetchFiles = async () => {
      try {
        const response = await api.get<UploadedFileListResponse[]>(
          "/materials/files"
        );
        setFiles(response.data.map(normalizeUploadedFile));
      } catch (error) {
        console.error("Failed to fetch uploaded files:", error);
      }
    };

    fetchSessions();
    fetchFiles();
  }, []); // Run only once on mount

  // Effect for polling file statuses
  useEffect(() => {
    const activePolls = new Map<number, ReturnType<typeof setInterval>>();

    const pollStatus = async (fileId: number) => {
      try {
        const response = await api.get<{ status: UploadedFileState["status"] }>(
          `/materials/${fileId}/status`
        );
        const newStatus = response.data.status;
        setFiles((prevFiles) =>
          prevFiles.map((f) =>
            f.id === fileId ? { ...f, status: newStatus } : f
          )
        );
        if (newStatus === "success" || newStatus === "failed") {
          clearInterval(activePolls.get(fileId));
          activePolls.delete(fileId);
        }
      } catch (error) {
        console.error(`Failed to poll status for file ${fileId}:`, error);
        clearInterval(activePolls.get(fileId));
        activePolls.delete(fileId);
      }
    };

    files.forEach((file) => {
      if (
        (file.status === "pending" || file.status === "processing") &&
        !activePolls.has(file.id)
      ) {
        const intervalId = setInterval(() => pollStatus(file.id), 3000);
        activePolls.set(file.id, intervalId);
      }
    });

    return () => {
      activePolls.forEach((intervalId) => clearInterval(intervalId));
    };
  }, [files]);

  const handleCreateSession = async () => {
    try {
      const response = await api.post<ChatSession>("/materials/chat/sessions");
      setSessions((prev) => [response.data, ...prev]);
      setActiveSessionId(response.data.id);
    } catch (error) {
      console.error("Failed to create session", error);
    }
  };

  const handleFileUpload = async (file: File) => {
    const formData = new FormData();
    formData.append("file_type", "pdf"); // Or derive from file type
    formData.append("file", file);
    formData.append("name", file.name);

    try {
      const response = await api.post<UploadedFileUploadResponse>(
        "/materials/file",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      const uploaded = normalizeUploadedFile(response.data);
      setFiles((prev) => {
        const deduped = prev.filter((fileItem) => fileItem.id !== uploaded.id);
        return [uploaded, ...deduped];
      });
    } catch (error) {
      console.error("Upload failed", error);
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white font-sans">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onCreateSession={handleCreateSession}
        files={files}
      />

      <main className="w-2/3 flex flex-col bg-[#1e1f22]">
        <div className="border-b border-zinc-800 px-4 pt-4">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveView("chat")}
              className={`rounded-t-xl px-4 py-2 text-sm font-medium transition-colors ${
                activeView === "chat"
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveView("quiz")}
              className={`rounded-t-xl px-4 py-2 text-sm font-medium transition-colors ${
                activeView === "quiz"
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              Quiz
            </button>
            <button
              onClick={() => setActiveView("flashcards")}
              className={`rounded-t-xl px-4 py-2 text-sm font-medium transition-colors ${
                activeView === "flashcards"
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              Flashcards
            </button>
          </div>
        </div>

        {activeView === "chat" ? (
          activeSessionId ? (
            <ChatInterface
              key={activeSessionId}
              sessionId={activeSessionId}
              allFiles={files}
              onFileUpload={handleFileUpload}
              selectedFileIds={selectedFileIds}
              onSelectFileForContext={setSelectedFileIds}
            />
          ) : (
            <div className="flex-grow flex items-center justify-center text-zinc-500">
              <p>Select or create a chat to begin.</p>
            </div>
          )
        ) : activeView === "flashcards" ? (
          <FlashcardWorkspace
            allFiles={files}
            selectedFileIds={selectedFileIds}
            onSelectFileForContext={setSelectedFileIds}
          />
        ) : (
          <QuizWorkspace
            allFiles={files}
            selectedFileIds={selectedFileIds}
            onSelectFileForContext={setSelectedFileIds}
          />
        )}
      </main>
    </div>
  );
}
