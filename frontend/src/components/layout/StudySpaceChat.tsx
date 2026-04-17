"use client";

import { useState } from "react";
import TopNav from "@/components/layout/TopNav";
import ContentPanel from "@/components/layout/ContentPanel";
import AIPanel from "@/components/layout/AIPanel";
import DocumentViewer from "@/components/viewers/DocumentViewer";
import QuizViewer from "@/components/viewers/QuizViewer";
import FlashcardViewer from "@/components/viewers/FlashcardViewer";
import UploadModal from "@/components/modals/UploadModal";
import CustomizeQuizModal from "@/components/modals/CustomizeQuizModal";
import CustomizeFlashcardsModal from "@/components/modals/CustomizeFlashcardsModal";

import { useFiles } from "@/hooks/useFiles";
import { useChatSessions } from "@/hooks/useChatSessions";
import { useAIGeneration } from "@/hooks/useAIGeneration";

export default function StudySpaceChat() {
  // Middle Column View State
  const [middleColumnView, setMiddleColumnView] = useState<"document" | "quiz" | "flashcard">("document");

  // Modal states
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isQuizModalOpen, setIsQuizModalOpen] = useState(false);
  const [isFlashcardsModalOpen, setIsFlashcardsModalOpen] = useState(false);

  // Custom Hooks
  const {
    files,
    viewingFileId,
    viewingFile,
    selectedFileIds,
    setSelectedFileIds,
    handleFileUpload,
    handleFileClick,
    handleSelectAllFiles,
    handleSelectFile
  } = useFiles(setMiddleColumnView);

  const {
    sessions,
    activeSessionId,
    setActiveSessionId,
    handleCreateSession
  } = useChatSessions();

  const {
    quizzes,
    decks,
    activeQuizId,
    setActiveQuizId,
    activeDeckId,
    setActiveDeckId,
    handleCreateQuiz,
    handleCreateFlashcards
  } = useAIGeneration(selectedFileIds, setMiddleColumnView);

  return (
    <div className="flex flex-col h-screen bg-black text-white font-sans overflow-hidden">
      <TopNav title={middleColumnView === "document" ? (viewingFile?.name || "Study Space") : "Study Space"} />

      <div className="flex flex-grow min-h-0">
        <ContentPanel
          files={files}
          selectedFileIds={selectedFileIds}
          onSelectFile={handleSelectFile}
          onSelectAll={handleSelectAllFiles}
          onAddContent={() => setIsUploadModalOpen(true)}
          onFileClick={handleFileClick}
          viewingFileId={middleColumnView === "document" ? viewingFileId : null}
        />

        <main className="flex-grow flex flex-col min-w-0 bg-[#09090b]">
          {middleColumnView === "document" && viewingFileId && viewingFile && (
            <DocumentViewer
              key={`doc-${viewingFileId}`}
              fileId={viewingFileId}
              fileName={viewingFile.name}
              onClose={() => setMiddleColumnView("document")}
            />
          )}
          
          {middleColumnView === "quiz" && activeQuizId && (
            <QuizViewer 
              key={`quiz-${activeQuizId}`}
              quizId={activeQuizId} 
              onClose={() => setMiddleColumnView("document")} 
            />
          )}
          
          {middleColumnView === "flashcard" && activeDeckId && (
            <FlashcardViewer 
              key={`deck-${activeDeckId}`}
              deckId={activeDeckId} 
              onClose={() => setMiddleColumnView("document")} 
            />
          )}

          {middleColumnView === "document" && !viewingFileId && (
            <div className="flex-grow flex items-center justify-center text-zinc-600 bg-[#1e1f22]">
              <p>Select a document from the Content panel to view it here.</p>
            </div>
          )}
        </main>

        <AIPanel
          files={files}
          selectedFileIds={selectedFileIds}
          onSelectFileForContext={setSelectedFileIds}
          onFileUpload={handleFileUpload}
          activeSessionId={activeSessionId}
          sessions={sessions}
          onSelectSession={setActiveSessionId}
          onCreateSession={handleCreateSession}
          onOpenQuizModal={() => setIsQuizModalOpen(true)}
          onOpenFlashcardsModal={() => setIsFlashcardsModalOpen(true)}
          quizzes={quizzes}
          decks={decks}
          onQuizClick={(id) => {
            setActiveQuizId(id);
            setMiddleColumnView("quiz");
          }}
          onDeckClick={(id) => {
            setActiveDeckId(id);
            setMiddleColumnView("flashcard");
          }}
        />
      </div>

      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUpload={handleFileUpload}
      />
      
      <CustomizeQuizModal
        isOpen={isQuizModalOpen}
        onClose={() => setIsQuizModalOpen(false)}
        onCreate={(config) => {
          handleCreateQuiz(config);
          setIsQuizModalOpen(false);
        }}
      />
      
      <CustomizeFlashcardsModal
        isOpen={isFlashcardsModalOpen}
        onClose={() => setIsFlashcardsModalOpen(false)}
        onCreate={(config) => {
          handleCreateFlashcards(config);
          setIsFlashcardsModalOpen(false);
        }}
      />
    </div>
  );
}
