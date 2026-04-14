"use client";

import React, { useState, useRef } from "react";
import { Paperclip, ArrowUp, XCircle, Loader2 } from "lucide-react";
import type { UploadedFileState } from "@/components/StudySpaceChat";

interface ChatInputBarProps {
  onChatSubmit: (query: string) => void;
  onFileUpload: (file: File) => Promise<void>;
  isLoading: boolean;
  readyFiles: UploadedFileState[];
  selectedFileIds: Set<number>;
  onSelectFileForContext: React.Dispatch<React.SetStateAction<Set<number>>>;
}

// Chat input bar component
const ChatInputBar: React.FC<ChatInputBarProps> = ({
  onChatSubmit,
  onFileUpload,
  isLoading,
  readyFiles,
  selectedFileIds,
  onSelectFileForContext,
}) => {
  
  // State for the query, file to upload, and uploading status
  const [query, setQuery] = useState("");
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleLocalSubmit = () => {
    onChatSubmit(query);
    setQuery("");
  };

  // Handle key down
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (query.trim()) {
        handleLocalSubmit();
      }
    }
  };

  // Handle file select
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileToUpload(file);
    }
    e.target.value = "";
  };

  // Handle upload click
  const handleUploadClick = async () => {
    if (!fileToUpload) return;
    setIsUploading(true);
    await onFileUpload(fileToUpload);
    setIsUploading(false);
    setFileToUpload(null);
  };

  return (
    <div className="bg-[#282a2e] rounded-2xl p-4 shadow-lg flex flex-col gap-3">
      {/* Section for selecting files for context */}
      {readyFiles.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 border-b border-zinc-700 pb-3">
          <span className="text-xs text-zinc-400 font-medium mr-2">
            Context:
          </span>
          {readyFiles.map((file) => (
            <button
              key={file.id}
              onClick={() =>
                onSelectFileForContext((prev) => {
                  const next = new Set(prev);
                  next.has(file.id) ? next.delete(file.id) : next.add(file.id);
                  return next;
                })
              }
              className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
                selectedFileIds.has(file.id)
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-700 hover:bg-zinc-600 text-zinc-200"
              }`}
            >
              {file.name}
            </button>
          ))}
        </div>
      )}

      {/* Section for a file pending upload */}
      {fileToUpload && (
        <div className="flex items-center justify-between text-sm bg-zinc-700/50 px-3 py-2 rounded-md">
          <div className="flex items-center gap-2 overflow-hidden">
            <Paperclip size={16} className="text-zinc-300 flex-shrink-0" />
            <span className="truncate text-zinc-100">{fileToUpload.name}</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleUploadClick}
              disabled={isUploading}
              className="text-xs font-semibold bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded-md disabled:bg-zinc-600"
            >
              {isUploading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                "Upload"
              )}
            </button>
            <button
              onClick={() => setFileToUpload(null)}
              disabled={isUploading}
            >
              <XCircle size={20} className="text-zinc-400 hover:text-white" />
            </button>
          </div>
        </div>
      )}

      {/* Main input and send button */}
      <div className="flex items-start gap-2">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="text-gray-400 hover:text-white transition-colors p-2"
          title="Attach file"
        >
          <Paperclip size={22} />
        </button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          className="hidden"
          accept=".pdf,.txt,.md"
        />
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          className="w-full bg-transparent text-gray-200 placeholder-gray-500 focus:outline-none resize-none text-base mt-1.5"
          rows={1}
          disabled={isLoading}
        />
        <button
          onClick={handleLocalSubmit}
          className="bg-white hover:bg-gray-200 transition-colors text-black rounded-full p-2 disabled:bg-gray-600 disabled:cursor-not-allowed"
          disabled={!query.trim() || isLoading}
          title="Send message"
        >
          <ArrowUp size={20} />
        </button>
      </div>
    </div>
  );
};

export default ChatInputBar;
