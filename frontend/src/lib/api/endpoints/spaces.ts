/**
 * Spaces endpoints — centralized definitions.
 * Every space-related API path is defined here ONCE.
 */

import type { Fetcher } from "../types";
import type {
  Space,
  SpaceListItem,
  ExploreSpaceItem,
  SpaceCreatePayload,
  SpaceUpdatePayload,
} from "@/types/space";
import type { UploadedFileListResponse, ChatSession } from "@/types/dashboard";
import type { QuizSummary } from "@/types/quiz";
import type { FlashcardDeckSummary } from "@/types/flashcard";
import type { VideoListItem } from "@/types/video";

export function createSpacesApi(fetcher: Fetcher) {
  return {
    // ── Space CRUD ──────────────────────────────

    /** GET /spaces — List all user spaces */
    list: () =>
      fetcher<SpaceListItem[]>("/spaces"),

    /** POST /spaces — Create a new space */
    create: (payload: SpaceCreatePayload) =>
      fetcher<Space>("/spaces", {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    /** GET /spaces/{spaceId} — Get single space details */
    get: (spaceId: number) =>
      fetcher<Space>(`/spaces/${spaceId}`),

    /** PUT /spaces/{spaceId} — Update a space */
    update: (spaceId: number, payload: SpaceUpdatePayload) =>
      fetcher<Space>(`/spaces/${spaceId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      }),

    /** DELETE /spaces/{spaceId} — Delete a space */
    delete: (spaceId: number) =>
      fetcher<void>(`/spaces/${spaceId}`, { method: "DELETE" }),

    /** GET /spaces/explore — Discover public spaces */
    explore: (query?: string, limit?: number, offset?: number) => {
      const params = new URLSearchParams();
      if (query) params.set("query", query);
      if (limit !== undefined) params.set("limit", String(limit));
      if (offset !== undefined) params.set("offset", String(offset));
      const qs = params.toString();
      return fetcher<ExploreSpaceItem[]>(`/spaces/explore${qs ? `?${qs}` : ""}`);
    },

    // ── Space-scoped resource listing ───────────

    /** GET /spaces/{spaceId}/materials/files — List files for a space */
    listFiles: (spaceId: number) =>
      fetcher<UploadedFileListResponse[]>(`/spaces/${spaceId}/materials/files`),

    /** GET /spaces/{spaceId}/materials/chat/sessions — List chat sessions for a space */
    listChatSessions: (spaceId: number) =>
      fetcher<ChatSession[]>(`/spaces/${spaceId}/materials/chat/sessions`),

    /** GET /spaces/{spaceId}/materials/quizzes — List quizzes for a space */
    listQuizzes: (spaceId: number) =>
      fetcher<QuizSummary[]>(`/spaces/${spaceId}/materials/quizzes`),

    /** GET /spaces/{spaceId}/materials/flashcards — List flashcard decks for a space */
    listFlashcards: (spaceId: number) =>
      fetcher<FlashcardDeckSummary[]>(`/spaces/${spaceId}/materials/flashcards`),

    /** GET /spaces/{spaceId}/videos — List videos for a space */
    listVideos: (spaceId: number) =>
      fetcher<VideoListItem[]>(`/spaces/${spaceId}/videos`),
  };
}
