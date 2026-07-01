"use server";

import { api } from "@/lib/api/index.server";
import { isNextRedirectError } from "@/lib/api/transport.server";
import type { ActionResult } from "@/types";

export async function createChatSessionAction(spaceId: number): Promise<ActionResult<any>> {
  try {
    const data = await api.spaces.createChatSession(spaceId);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to create chat session",
      data: null,
    };
  }
}
