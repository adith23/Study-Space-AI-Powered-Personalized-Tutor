"use server";

import { api } from "@/lib/api/index.server";
import { isNextRedirectError } from "@/lib/api/transport.server";
import type { CreateFlashcardDeckPayload } from "@/types/flashcard";
import type { ActionResult } from "@/types";

export async function createFlashcardDeckAction(
  spaceId: number,
  payload: CreateFlashcardDeckPayload,
): Promise<ActionResult<any>> {
  try {
    const data = await api.spaces.createFlashcardDeck(spaceId, payload);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to create flashcard deck",
      data: null,
    };
  }
}
