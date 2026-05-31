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
import {
  formatVideoSubtitle,
  getVideoRendererLabel,
} from "@/lib/videoPresentation";
import type { UploadedFileState, ChatSession } from "@/types/dashboard";
import type { QuizSummary } from "@/types/quiz";
import type { FlashcardDeckSummary } from "@/types/flashcard";
import type { VideoListItem } from "@/types/video";

interface AIPanelProps {
  files: UploadedFileState[];
  selectedFileIds: Set<number>;
  onSelectFileForContext: React.Dispatch<React.SetStateAction<Set<number>>>;
  onFileUpload: (file: File) => Promise<void>;
  activeSessionId: string | null;
  sessions: ChatSession[];
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;
  onOpenQuizModal: () => void;
  onOpenFlashcardsModal: () => void;
  onOpenVideoModal: () => void;
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
    <aside className="flex w-[400px] shrink-0 flex-col border-l border-zinc-800 bg-[#1e1f22]">
      <div className="flex items-center justify-between border-b border-zinc-800 p-4">
        <div className="flex rounded-full bg-zinc-800/50 p-1">
          <button
            onClick={() => setActiveTab("ai_content")}
            className={`flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
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
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              activeTab === "chat"
                ? "bg-zinc-700 text-white"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            Chat
          </button>
        </div>
        <button className="text-zinc-400 transition-colors hover:text-white">
          <ChevronsRight size={18} />
        </button>
      </div>

      <div className="relative flex flex-grow flex-col overflow-y-auto">
        {activeTab === "ai_content" ? (
          <div className="space-y-6 p-4">
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={onOpenQuizModal}
                className="group flex items-center justify-between rounded-xl border border-zinc-700 bg-zinc-800/80 p-3 transition-colors hover:bg-zinc-700"
              >
                <div className="flex items-center gap-3">
                  <Map size={18} className="text-blue-400" />
                  <span className="text-sm font-medium text-white">Quiz</span>
                </div>
                <div className="flex h-6 w-6 items-center justify-center rounded border border-zinc-600 opacity-0 transition-opacity group-hover:opacity-100">
                  <span className="text-[10px] text-zinc-400">⌘Q</span>
                </div>
              </button>
              <button
                onClick={onOpenFlashcardsModal}
                className="group flex items-center justify-between rounded-xl border border-zinc-700 bg-zinc-800/80 p-3 transition-colors hover:bg-zinc-700"
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
                className="group flex items-center justify-between rounded-xl border border-zinc-700 bg-zinc-800/80 p-3 transition-colors hover:bg-zinc-700"
              >
                <div className="flex items-center gap-3">
                  <PlayCircle size={18} className="text-red-400" />
                  <span className="text-sm font-medium text-white">
                    Video Explainer
                  </span>
                </div>
              </button>
              <button className="group flex items-center justify-between rounded-xl border border-zinc-700 bg-zinc-800/80 p-3 transition-colors hover:bg-zinc-700">
                <div className="flex items-center gap-3">
                  <Headphones size={18} className="text-blue-300" />
                  <span className="text-sm font-medium text-white">
                    Audio Explainer
                  </span>
                </div>
              </button>
              <button className="group flex items-center justify-between rounded-xl border border-zinc-700 bg-zinc-800/80 p-3 transition-colors hover:bg-zinc-700">
                <div className="flex items-center gap-3">
                  <FileText size={18} className="text-yellow-400" />
                  <span className="text-sm font-medium text-white">
                    Summary Info
                  </span>
                </div>
              </button>
            </div>

            <div className="mt-8 space-y-2">
              {quizzes.length === 0 && decks.length === 0 && videos.length === 0 && (
                <p className="py-4 text-center text-sm text-zinc-500">
                  No content generated yet.
                </p>
              )}

              {quizzes.map((quiz) => (
                <div
                  key={`quiz-${quiz.id}`}
                  onClick={() => onQuizClick(quiz.id)}
                  className="group flex cursor-pointer items-center justify-between rounded-xl p-3 transition-colors hover:bg-zinc-800/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-blue-500/20 p-2 text-blue-400">
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
                  <button className="rounded p-1 text-zinc-500 opacity-0 transition-all hover:bg-zinc-700 hover:text-white group-hover:opacity-100">
                    <MoreVertical size={16} />
                  </button>
                </div>
              ))}

              {decks.map((deck) => (
                <div
                  key={`deck-${deck.id}`}
                  onClick={() => onDeckClick(deck.id)}
                  className="group flex cursor-pointer items-center justify-between rounded-xl p-3 transition-colors hover:bg-zinc-800/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-green-500/20 p-2 text-green-400">
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
                  <button className="rounded p-1 text-zinc-500 opacity-0 transition-all hover:bg-zinc-700 hover:text-white group-hover:opacity-100">
                    <MoreVertical size={16} />
                  </button>
                </div>
              ))}

              {videos.map((video) => (
                <div
                  key={`video-${video.id}`}
                  onClick={() => onVideoClick(video.id)}
                  className="group flex cursor-pointer items-center justify-between rounded-xl p-3 transition-colors hover:bg-zinc-800/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-red-500/20 p-2 text-red-400">
                      <PlayCircle size={20} />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-white">
                        {video.title || `Video ${video.id}`}
                      </h4>
                      <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
                        <span>{formatVideoSubtitle(video)}</span>
                        <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-[10px] uppercase tracking-wide text-zinc-300">
                          {getVideoRendererLabel(video.renderer)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button className="rounded p-1 text-zinc-500 opacity-0 transition-all hover:bg-zinc-700 hover:text-white group-hover:opacity-100">
                    <MoreVertical size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-grow flex-col">
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
              <div className="flex flex-grow flex-col items-center justify-center p-4">
                <p className="mb-4 text-sm text-zinc-500">No chat selected.</p>
                {sessions.length > 0 ? (
                  <div className="w-full max-w-xs space-y-2">
                    {sessions.map((s) => (
                      <button
                        key={s.id}
                        onClick={() => onSelectSession(s.id)}
                        className="w-full rounded-lg bg-zinc-800 px-4 py-2 text-left text-sm text-white transition-colors hover:bg-zinc-700"
                      >
                        {s.name}
                      </button>
                    ))}
                  </div>
                ) : (
                  <button
                    onClick={onCreateSession}
                    className="rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                  >
                    Start a New Chat
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {activeTab === "ai_content" && (
        <div className="border-t border-zinc-800 p-4">
          <div className="flex items-center gap-2 rounded-full border border-zinc-700 bg-transparent px-4 py-2 transition-colors focus-within:border-zinc-500 focus-within:bg-zinc-900">
            <input
              type="text"
              value={chatQuery}
              onChange={(e) => setChatQuery(e.target.value)}
              placeholder="Start typing..."
              className="flex-grow bg-transparent text-sm text-white placeholder-zinc-500 focus:outline-none"
            />
            {selectedFileIds.size > 0 && (
              <span className="whitespace-nowrap text-xs font-medium text-zinc-400">
                {selectedFileIds.size} source
                {selectedFileIds.size > 1 ? "s" : ""}
              </span>
            )}
            <button className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-zinc-700 text-zinc-300 transition-colors hover:bg-zinc-600 hover:text-white">
              <Send size={12} />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
};

export default AIPanel;
