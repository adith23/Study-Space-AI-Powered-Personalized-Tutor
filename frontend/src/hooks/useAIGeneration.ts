import { useState } from "react";
import { createQuizAction } from "@/actions/quiz";
import { createFlashcardDeckAction } from "@/actions/flashcard";
import type { QuizSummary } from "@/types/quiz";
import type { FlashcardDeckSummary } from "@/types/flashcard";

export function useAIGeneration(
  spaceId: number,
  initialQuizzes: QuizSummary[],
  initialDecks: FlashcardDeckSummary[],
  selectedFileIds: Set<number>,
  setMiddleColumnView: (view: "document" | "quiz" | "flashcard") => void,
) {
  const [quizzes, setQuizzes] = useState<QuizSummary[]>(initialQuizzes);
  const [decks, setDecks] = useState<FlashcardDeckSummary[]>(initialDecks);
  const [activeQuizId, setActiveQuizId] = useState<number | null>(null);
  const [activeDeckId, setActiveDeckId] = useState<number | null>(null);

  const handleCreateQuiz = async (config: {
    questionCount: string;
    difficulty: string;
    focus: string;
  }) => {
    const fileIds = Array.from(selectedFileIds);
    if (fileIds.length === 0) {
      alert("Select at least one processed source for quiz generation.");
      return;
    }

    let count = 5;
    if (config.questionCount === "Fewer") count = 3;
    if (config.questionCount === "More") count = 10;

    try {
      const result = await createQuizAction(spaceId, {
        file_ids: fileIds,
        number_of_questions: count,
        difficulty_level: config.difficulty.toLowerCase() as any,
        focus_prompt: config.focus.trim() || null,
        title: null,
      });

      if (result.error || !result.data) {
        alert(result.error || "Failed to create quiz.");
        return;
      }

      const quiz = result.data as QuizSummary;
      setQuizzes((prev) => [
        quiz,
        ...prev.filter((item) => item.id !== quiz.id),
      ]);
      setActiveQuizId(quiz.id);
      setMiddleColumnView("quiz");
    } catch (error) {
      console.error("Failed to create quiz", error);
      alert("Failed to create quiz.");
    }
  };

  const handleCreateFlashcards = async (config: {
    questionCount: string;
    difficulty: string;
    focus: string;
  }) => {
    const fileIds = Array.from(selectedFileIds);
    if (fileIds.length === 0) {
      alert("Select at least one processed source for flashcard generation.");
      return;
    }

    let count = 10;
    if (config.questionCount === "Fewer") count = 5;
    if (config.questionCount === "More") count = 20;

    try {
      const result = await createFlashcardDeckAction(spaceId, {
        file_ids: fileIds,
        number_of_cards: count,
        difficulty_level: config.difficulty.toLowerCase() as any,
        focus_prompt: config.focus.trim() || null,
        title: null,
      });

      if (result.error || !result.data) {
        alert(result.error || "Failed to create flashcards.");
        return;
      }

      const deck = result.data as FlashcardDeckSummary;
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
    handleCreateFlashcards,
  };
}
