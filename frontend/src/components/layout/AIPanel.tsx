import React, { useState } from "react";
import {
  ChevronsRight,
  MoreVertical,
  PlayCircle,
  Headphones,
  FileText,
  Map,
  Send,
} from "lucide-react";
import ChatInterface from "@/components/chat/ChatInterface";
import type { UploadedFileState, ChatSession } from "@/types/dashboard";
import type { QuizSummary } from "@/types/quiz";
import type { FlashcardDeckSummary } from "@/types/flashcard";
import type { VideoListItem } from "@/types/video";

interface AIPanelProps {
  files: UploadedFileState[];
  selectedFileIds: Set<number>;
  onSelectFileForContext: React.Dispatch<React.SetStateAction<Set<number>>>;
  onFileUpload: (file: File) => Promise<void>;

  // Chat props
  activeSessionId: string | null;
  sessions: ChatSession[];
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;

  // Action handlers
  onOpenQuizModal: () => void;
  onOpenFlashcardsModal: () => void;
  onOpenVideoModal: () => void;

  // Generated Items
  quizzes: QuizSummary[];
  decks: FlashcardDeckSummary[];
  videos: VideoListItem[];
  onQuizClick: (id: number) => void;
  onDeckClick: (id: number) => void;
  onVideoClick: (id: number) => void;
}

const AIPanel: React.FC<AIPanelProps> = ({
  files,
  selectedFileIds,
  onSelectFileForContext,
  onFileUpload,
  activeSessionId,
  sessions,
  onSelectSession,
  onCreateSession,
  onOpenQuizModal,
  onOpenFlashcardsModal,
  onOpenVideoModal,
  quizzes,
  decks,
  videos,
  onQuizClick,
  onDeckClick,
  onVideoClick,
}) => {
  const [activeTab, setActiveTab] = useState<"ai_content" | "chat">(
    "ai_content",
  );
  const [chatQuery, setChatQuery] = useState("");

  return (
    <aside className="flex flex-col w-[400px] bg-[#1e1f22] border-l border-zinc-800 shrink-0">
      {/* Header Tabs */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800">
        <div className="flex bg-zinc-800/50 p-1 rounded-full">
          <button
            onClick={() => setActiveTab("ai_content")}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              activeTab === "ai_content"
                ? "bg-zinc-700 text-white"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            {activeTab === "ai_content" && (
              <span className="h-2 w-2 rounded-full bg-green-500" />
            )}
            AI Content
          </button>
          <button
            onClick={() => setActiveTab("chat")}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              activeTab === "chat"
                ? "bg-zinc-700 text-white"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            Chat
          </button>
        </div>
        <button className="text-zinc-400 hover:text-white transition-colors">
          <ChevronsRight size={18} />
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-grow overflow-y-auto flex flex-col relative">
        {activeTab === "ai_content" ? (
          <div className="p-4 space-y-6">
            {/* Action Buttons Grid */}
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={onOpenQuizModal}
                className="flex items-center justify-between p-3 rounded-xl bg-zinc-800/80 border border-zinc-700 hover:bg-zinc-700 transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <Map size={18} className="text-blue-400" />
                  <span className="text-sm font-medium text-white">Quiz</span>
                </div>
                <div className="w-6 h-6 rounded border border-zinc-600 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="text-[10px] text-zinc-400">⌘Q</span>
                </div>
              </button>
              <button
                onClick={onOpenFlashcardsModal}
                className="flex items-center justify-between p-3 rounded-xl bg-zinc-800/80 border border-zinc-700 hover:bg-zinc-700 transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <FileText size={18} className="text-green-400" />
                  <span className="text-sm font-medium text-white">
                    Flashcards
                  </span>
                </div>
              </button>
              <button
                onClick={onOpenVideoModal}
                className="flex items-center justify-between p-3 rounded-xl bg-zinc-800/80 border border-zinc-700 hover:bg-zinc-700 transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <PlayCircle size={18} className="text-red-400" />
                  <span className="text-sm font-medium text-white">
                    Video Explainer
                  </span>
                </div>
              </button>
              <button className="flex items-center justify-between p-3 rounded-xl bg-zinc-800/80 border border-zinc-700 hover:bg-zinc-700 transition-colors group">
                <div className="flex items-center gap-3">
                  <Headphones size={18} className="text-blue-300" />
                  <span className="text-sm font-medium text-white">
                    Audio Explainer
                  </span>
                </div>
              </button>
              <button className="flex items-center justify-between p-3 rounded-xl bg-zinc-800/80 border border-zinc-700 hover:bg-zinc-700 transition-colors group">
                <div className="flex items-center gap-3">
                  <FileText size={18} className="text-yellow-400" />
                  <span className="text-sm font-medium text-white">
                    Summary Info
                  </span>
                </div>
              </button>
            </div>

            {/* Generated Items List */}
            <div className="space-y-2 mt-8">
              {quizzes.length === 0 && decks.length === 0 && (
                <p className="text-sm text-zinc-500 text-center py-4">
                  No content generated yet.
                </p>
              )}

              {quizzes.map((quiz) => (
                <div
                  key={`quiz-${quiz.id}`}
                  onClick={() => onQuizClick(quiz.id)}
                  className="flex items-center justify-between p-3 rounded-xl hover:bg-zinc-800/50 transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
                      <Map size={20} />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-white">
                        {quiz.title || `Quiz ${quiz.id}`}
                      </h4>
                      <p className="text-xs text-zinc-500">
                        {quiz.number_of_questions} Questions |{" "}
                        {quiz.difficulty_level}
                      </p>
                    </div>
                  </div>
                  <button className="p-1 rounded text-zinc-500 hover:text-white hover:bg-zinc-700 opacity-0 group-hover:opacity-100 transition-all">
                    <MoreVertical size={16} />
                  </button>
                </div>
              ))}

              {decks.map((deck) => (
                <div
                  key={`deck-${deck.id}`}
                  onClick={() => onDeckClick(deck.id)}
                  className="flex items-center justify-between p-3 rounded-xl hover:bg-zinc-800/50 transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-green-500/20 text-green-400">
                      <FileText size={20} />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-white">
                        {deck.title || `Flashcards ${deck.id}`}
                      </h4>
                      <p className="text-xs text-zinc-500">
                        {deck.number_of_cards} Cards | {deck.difficulty_level}
                      </p>
                    </div>
                  </div>
                  <button className="p-1 rounded text-zinc-500 hover:text-white hover:bg-zinc-700 opacity-0 group-hover:opacity-100 transition-all">
                    <MoreVertical size={16} />
                  </button>
                </div>
              ))}

              {videos.map((video) => (
                <div
                  key={`video-${video.id}`}
                  onClick={() => onVideoClick(video.id)}
                  className="flex items-center justify-between p-3 rounded-xl hover:bg-zinc-800/50 transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-red-500/20 text-red-400">
                      <PlayCircle size={20} />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-white">
                        {video.title || `Video ${video.id}`}
                      </h4>
                      <p className="text-xs text-zinc-500">
                        {video.duration_seconds
                          ? `${Math.floor(video.duration_seconds / 60)}:${String(Math.floor(video.duration_seconds % 60)).padStart(2, "0")}`
                          : video.style || "Video"}{" "}
                        | {video.status}
                      </p>
                    </div>
                  </div>
                  <button className="p-1 rounded text-zinc-500 hover:text-white hover:bg-zinc-700 opacity-0 group-hover:opacity-100 transition-all">
                    <MoreVertical size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Chat Interface */
          <div className="flex-grow flex flex-col">
            {activeSessionId ? (
              <ChatInterface
                key={activeSessionId}
                sessionId={activeSessionId}
                allFiles={files}
                onFileUpload={onFileUpload}
                selectedFileIds={selectedFileIds}
                onSelectFileForContext={onSelectFileForContext}
              />
            ) : (
              <div className="flex-grow flex flex-col items-center justify-center p-4">
                <p className="text-sm text-zinc-500 mb-4">No chat selected.</p>
                {sessions.length > 0 ? (
                  <div className="space-y-2 w-full max-w-xs">
                    {sessions.map((s) => (
                      <button
                        key={s.id}
                        onClick={() => onSelectSession(s.id)}
                        className="w-full text-left px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-sm text-white transition-colors"
                      >
                        {s.name}
                      </button>
                    ))}
                  </div>
                ) : (
                  <button
                    onClick={onCreateSession}
                    className="px-4 py-2 rounded-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
                  >
                    Start a New Chat
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Persistent Bottom Input Bar for AI Content Tab */}
      {activeTab === "ai_content" && (
        <div className="p-4 border-t border-zinc-800">
          <div className="flex items-center gap-2 bg-transparent border border-zinc-700 rounded-full px-4 py-2 focus-within:border-zinc-500 focus-within:bg-zinc-900 transition-colors">
            <input
              type="text"
              value={chatQuery}
              onChange={(e) => setChatQuery(e.target.value)}
              placeholder="Start typing..."
              className="flex-grow bg-transparent text-sm text-white placeholder-zinc-500 focus:outline-none"
            />
            {selectedFileIds.size > 0 && (
              <span className="text-xs text-zinc-400 font-medium whitespace-nowrap">
                {selectedFileIds.size} source
                {selectedFileIds.size > 1 ? "s" : ""}
              </span>
            )}
            <button className="flex h-6 w-6 items-center justify-center rounded-full bg-zinc-700 text-zinc-300 hover:bg-zinc-600 hover:text-white transition-colors shrink-0">
              <Send size={12} />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
};

export default AIPanel;
