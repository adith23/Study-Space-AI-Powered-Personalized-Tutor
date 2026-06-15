/**
 * Client-side API — wires all endpoint definitions to the client transport.
 *
 * Import this ONLY in "use client" components:
 *   - Hooks for polling (useFiles, useVideoGeneration)
 *   - Components for on-demand data (QuizViewer, FlashcardViewer, ChatInterface)
 *
 * Usage:
 *   import { clientApi } from "@/lib/api/index.client";
 *   const meta = await clientApi.video.getStatus(videoId);
 */

import { clientTransport } from "./transport.client";
import { createFilesApi } from "./endpoints/files";
import { createChatApi } from "./endpoints/chat";
import { createQuizApi } from "./endpoints/quiz";
import { createFlashcardApi } from "./endpoints/flashcard";
import { createVideoApi } from "./endpoints/video";
import { createSpacesApi } from "./endpoints/spaces";

export const clientApi = {
  spaces: createSpacesApi(clientTransport),
  files: createFilesApi(clientTransport),
  chat: createChatApi(clientTransport),
  quiz: createQuizApi(clientTransport),
  flashcard: createFlashcardApi(clientTransport),
  video: createVideoApi(clientTransport),
};
