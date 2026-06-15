"use server";

import { api } from "@/lib/api/index.server";

export async function createChatSessionAction() {
  return api.chat.createSession();
}
