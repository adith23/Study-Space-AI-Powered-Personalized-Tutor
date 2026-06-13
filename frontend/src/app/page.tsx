import { api } from "@/lib/api/index.server";
import StudySpaceChat from "@/components/layout/StudySpaceChat";

import type { UploadedFileListResponse, ChatSession } from "@/types/dashboard";
import type { QuizSummary } from "@/types/quiz";
import type { FlashcardDeckSummary } from "@/types/flashcard";
import type { VideoListItem } from "@/types/video";

export default async function DashboardPage() {
  // All fetches run in parallel, server-to-server (< 1ms latency)
  const [files, sessions, quizzes, decks, videos] = await Promise.all([
    api.files.list().catch((): UploadedFileListResponse[] => []),
    api.chat.listSessions().catch((): ChatSession[] => []),
    api.quiz.list().catch((): QuizSummary[] => []),
    api.flashcard.list().catch((): FlashcardDeckSummary[] => []),
    api.video.list().catch((): VideoListItem[] => []),
  ]);

  return (
    <main className="h-screen w-screen bg-black overflow-hidden">
      <StudySpaceChat
        initialFiles={files}
        initialSessions={sessions}
        initialQuizzes={quizzes}
        initialDecks={decks}
        initialVideos={videos}
      />
    </main>
  );
}
