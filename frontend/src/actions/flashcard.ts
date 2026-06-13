"use server";

import { api } from "@/lib/api/index.server";
import type { CreateFlashcardDeckPayload } from "@/types/flashcard";

export async function createFlashcardDeckAction(
  payload: CreateFlashcardDeckPayload,
) {
  return api.flashcard.create(payload);
}
