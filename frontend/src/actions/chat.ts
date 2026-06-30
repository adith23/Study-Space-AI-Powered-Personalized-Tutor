"use server";

import { api } from "@/lib/api/index.server";

export async function createChatSessionAction(spaceId: number) {
  return api.spaces.createChatSession(spaceId);
}
