"use server";

import { api } from "@/lib/api/index.server";
import type { CreateFlashcardDeckPayload } from "@/types/flashcard";

export async function createFlashcardDeckAction(
  spaceId: number,
  payload: CreateFlashcardDeckPayload,
) {
  return api.spaces.createFlashcardDeck(spaceId, payload);
}
