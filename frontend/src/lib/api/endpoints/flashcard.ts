/**
 * Flashcard endpoints — centralized definitions.
 * Every flashcard-related API path is defined here ONCE.
 */

import type { Fetcher } from "../types";
import type {
  CreateFlashcardDeckPayload,
  FlashcardDeckSummary,
  FlashcardDeckDetail,
} from "@/types/flashcard";

export function createFlashcardApi(fetcher: Fetcher) {
  return {
    /** POST /materials/flashcards — Create a flashcard deck */
    create: (payload: CreateFlashcardDeckPayload) =>
      fetcher<FlashcardDeckSummary>("/materials/flashcards", {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    /** GET /materials/flashcards — List all flashcard decks */
    list: () =>
      fetcher<FlashcardDeckSummary[]>("/materials/flashcards"),

    /** GET /materials/flashcards/{id} — Get deck detail with cards */
    get: (deckId: number) =>
      fetcher<FlashcardDeckDetail>(`/materials/flashcards/${deckId}`),
  };
}
