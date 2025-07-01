import React, { useState, useRef } from "react";
import api from "../lib/api";
import {
  ChevronDown,
  BrainCircuit,
  Paperclip,
  Mic,
  ArrowUp,
  XCircle,
} from "lucide-react";

// Define the file types for the dropdown
const fileTypes = [
  "notes",
  "syllabus",
  "pdf",
  "book",
  "video",
  "web_link",
  "youtube",
];

// Main App Component for display
export default function MaterialUpload() {
  // State from original MaterialUpload
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState("notes");
  const [statusMessage, setStatusMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [isTypeDropdownOpen, setIsTypeDropdownOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const urlRegex = /^(https?:\/\/[^\s$.?#].[^\s]*)$/i;

  const handleSubmit = async () => {
    // If loading or no content, do nothing
    if (isLoading || (!message.trim() && !file)) {
      return;
    }

    const formData = new FormData();
    const isUrl = urlRegex.test(message.trim());
    formData.append("file_type", fileType);

    if (file) {
      formData.append("file", file);
    }

    if (isUrl) {
      formData.append("url", message.trim());
    }

    setIsLoading(true);
    setStatusMessage("");
    setIsError(false);

    try {
      await api.post("/materials/file", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setStatusMessage(`Successfully uploaded!`);
      setIsError(false);

      // Reset state after successful upload
      setMessage("");
      setFile(null);
    } catch (error: any) {
      setIsError(true);
      console.error("Axios Error:", error);

      // Detailed error handling
      const errorDetail = error?.response?.data?.detail;
      if (typeof errorDetail === "string") {
        setStatusMessage(`Upload Failed: ${errorDetail}`);
      } else if (Array.isArray(errorDetail)) {
        const formattedErrors = errorDetail
          .map((err) => `${err.loc.join("->")}: ${err.msg}`)
          .join(", ");
        setStatusMessage(`Upload Failed: ${formattedErrors}`);
      } else {
        setStatusMessage(
          "An unknown error occurred. Check the console for details."
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] ?? null;
    setFile(selectedFile);
    if (e.target) e.target.value = "";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-2xl">
      {/* Main container for the chat input */}
      <div className="bg-[#1e1f22] rounded-2xl p-4 shadow-lg text-white border border-zinc-700 relative">
        <div className="flex flex-col">
          {/* Textarea for user input */}
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter a name or paste a URL..."
            className="bg-transparent w-full text-base text-zinc-200 placeholder-zinc-500 focus:outline-none resize-none h-20"
            disabled={isLoading}
          />

          {/* Display selected file name if it exists */}
          {file && (
            <div className="mt-2 flex items-center gap-2 text-sm bg-zinc-700/50 px-3 py-1.5 rounded-lg w-fit">
              <Paperclip size={16} className="text-zinc-400" />
              <span className="text-zinc-200">{file.name}</span>
              <button onClick={() => setFile(null)} disabled={isLoading}>
                <XCircle size={18} className="text-zinc-500 hover:text-white" />
              </button>
            </div>
          )}

          {/* Toolbar section */}
          <div className="flex items-center justify-between mt-2">
            {/* Left side of the toolbar */}
            <div className="flex items-center gap-2">
              {/* File Type Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setIsTypeDropdownOpen(!isTypeDropdownOpen)}
                  className="flex items-center gap-1 text-zinc-300 hover:bg-zinc-700 px-3 py-1 rounded-md text-sm transition-colors capitalize"
                  disabled={isLoading}
                >
                  {fileType}
                  <ChevronDown size={16} />
                </button>
                {isTypeDropdownOpen && (
                  <div className="absolute bottom-full mb-2 bg-zinc-800 border border-zinc-700 rounded-lg shadow-xl py-1 w-32 z-10">
                    {fileTypes.map((type) => (
                      <button
                        key={type}
                        onClick={() => {
                          setFileType(type);
                          setIsTypeDropdownOpen(false);
                        }}
                        className="w-full text-left px-3 py-1.5 hover:bg-zinc-700 text-zinc-200 text-sm capitalize"
                      >
                        {type.replace("_", " ")}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <button
                className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-600 px-3 py-1.5 rounded-lg text-sm transition-colors"
                disabled={isLoading}
              >
                <BrainCircuit size={16} className="text-zinc-400" />
                Learn+
              </button>
            </div>

            {/* Right side of the toolbar */}
            <div className="flex items-center gap-3">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
                id="file-input"
                disabled={isLoading}
              />
              <button
                className="text-zinc-400 hover:text-white transition-colors"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
              >
                <Paperclip size={20} />
              </button>
              <button
                className="text-zinc-400 hover:text-white transition-colors"
                disabled={isLoading}
              >
                <Mic size={20} />
              </button>
              <button
                onClick={handleSubmit}
                className={`flex items-center justify-center w-8 h-8 rounded-full transition-colors ${
                  (message.trim() || file) && !isLoading
                    ? "bg-white text-black cursor-pointer"
                    : "bg-zinc-700 text-zinc-500 cursor-not-allowed"
                }`}
                disabled={(!message.trim() && !file) || isLoading}
              >
                {isLoading ? (
                  <svg
                    className="animate-spin h-5 w-5 text-black"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                ) : (
                  <ArrowUp size={20} />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
      {/* Status Message Display */}
      {statusMessage && (
        <div
          className={`mt-3 p-3 rounded-md text-sm break-words ${
            isError
              ? "bg-red-900/20 text-red-300 border border-red-500/30"
              : "bg-green-900/20 text-green-300 border border-green-500/30"
          }`}
        >
          {statusMessage}
        </div>
      )}
    </div>
  );
}
