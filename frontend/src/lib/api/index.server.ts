/**
 * Server-side API — wires all endpoint definitions to the server transport.
 *
 * Import this in:
 *   - Server Components (page.tsx, layout.tsx)
 *   - Server Actions (actions/*.ts)
 *   - Route Handlers (app/api/***route.ts) — for JSON endpoints only
 *
 * Usage:
 *   import { api } from "@/lib/api/index.server";
 *   const files = await api.files.list();
 */

import { serverTransport } from "./transport.server";
import { createFilesApi } from "./endpoints/files";
import { createChatApi } from "./endpoints/chat";
import { createQuizApi } from "./endpoints/quiz";
import { createFlashcardApi } from "./endpoints/flashcard";
import { createVideoApi } from "./endpoints/video";
import { createSpacesApi } from "./endpoints/spaces";

export const api = {
  spaces: createSpacesApi(serverTransport),
  files: createFilesApi(serverTransport),
  chat: createChatApi(serverTransport),
  quiz: createQuizApi(serverTransport),
  flashcard: createFlashcardApi(serverTransport),
  video: createVideoApi(serverTransport),
};
