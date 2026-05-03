import { useState, useEffect } from "react";
import { createQuiz, listQuizzes } from "@/lib/api/quiz";
import { createFlashcardDeck, listFlashcardDecks } from "@/lib/api/flashcard";
import type { QuizSummary } from "@/types/quiz";
import type { FlashcardDeckSummary } from "@/types/flashcard";

export function useAIGeneration(
  selectedFileIds: Set<number>, 
  setMiddleColumnView: (view: "document" | "quiz" | "flashcard") => void
) {
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [decks, setDecks] = useState<FlashcardDeckSummary[]>([]);
  const [activeQuizId, setActiveQuizId] = useState<number | null>(null);
  const [activeDeckId, setActiveDeckId] = useState<number | null>(null);

  useEffect(() => {
    const fetchGenerationData = async () => {
      try {
        const [quizzesRes, decksRes] = await Promise.all([
          listQuizzes().catch(() => []),
          listFlashcardDecks().catch(() => []),
        ]);
        setQuizzes(quizzesRes);
        setDecks(decksRes);
      } catch (error) {
        console.error("Failed to fetch initial generation data:", error);
      }
    };
    fetchGenerationData();
  }, []);

  const handleCreateQuiz = async (config: { questionCount: string, difficulty: string, focus: string }) => {
    const fileIds = Array.from(selectedFileIds);
    if (fileIds.length === 0) {
      alert("Select at least one processed source for quiz generation.");
      return;
    }

    let count = 5;
    if (config.questionCount === "Fewer") count = 3;
    if (config.questionCount === "More") count = 10;

    try {
      const quiz = await createQuiz({
        file_ids: fileIds,
        number_of_questions: count,
        difficulty_level: config.difficulty.toLowerCase() as any,
        focus_prompt: config.focus.trim() || null,
        title: null,
      });
      setQuizzes((prev) => [quiz, ...prev.filter((item) => item.id !== quiz.id)]);
      setActiveQuizId(quiz.id);
      setMiddleColumnView("quiz");
    } catch (error) {
      console.error("Failed to create quiz", error);
      alert("Failed to create quiz.");
    }
  };

  const handleCreateFlashcards = async (config: { questionCount: string, difficulty: string, focus: string }) => {
    const fileIds = Array.from(selectedFileIds);
    if (fileIds.length === 0) {
      alert("Select at least one processed source for flashcard generation.");
      return;
    }

    let count = 10;
    if (config.questionCount === "Fewer") count = 5;
    if (config.questionCount === "More") count = 20;

    try {
      const deck = await createFlashcardDeck({
        file_ids: fileIds,
        number_of_cards: count,
        difficulty_level: config.difficulty.toLowerCase() as any,
        focus_prompt: config.focus.trim() || null,
        title: null,
      });
      setDecks((prev) => [deck, ...prev.filter((item) => item.id !== deck.id)]);
      setActiveDeckId(deck.id);
      setMiddleColumnView("flashcard");
    } catch (error) {
      console.error("Failed to create flashcards", error);
      alert("Failed to create flashcards.");
    }
  };

  return {
    quizzes,
    decks,
    activeQuizId,
    setActiveQuizId,
    activeDeckId,
    setActiveDeckId,
    handleCreateQuiz,
    handleCreateFlashcards
  };
}
