import { api } from "./client";
import type {
  CreateFlashcardDeckPayload,
  FlashcardDeckDetail,
  FlashcardDeckSummary,
} from "@/types/flashcard";

export async function createFlashcardDeck(payload: CreateFlashcardDeckPayload) {
  const response = await api.post<FlashcardDeckSummary>(
    "/materials/flashcards",
    payload
  );
  return response.data;
}

export async function listFlashcardDecks() {
  const response = await api.get<FlashcardDeckSummary[]>(
    "/materials/flashcards"
  );
  return response.data;
}

export async function getFlashcardDeck(deckId: number) {
  const response = await api.get<FlashcardDeckDetail>(
    `/materials/flashcards/${deckId}`
  );
  return response.data;
}
