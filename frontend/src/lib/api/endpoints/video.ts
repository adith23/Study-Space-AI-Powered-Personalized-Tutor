/**
 * Video endpoints — centralized definitions.
 * Every video-related API path is defined here ONCE.
 */

import type { Fetcher } from "../types";
import type {
  VideoGenerateRequest,
  VideoGenerateResponse,
  VideoListItem,
  VideoMeta,
} from "@/types/video";

export function createVideoApi(fetcher: Fetcher) {
  return {
    /** POST /videos/generate — Start video generation */
    generate: (payload: VideoGenerateRequest) =>
      fetcher<VideoGenerateResponse>("/videos/generate", {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    /** GET /videos — List all videos */
    list: () =>
      fetcher<VideoListItem[]>("/videos"),

    /** GET /videos/{id} — Get video status/metadata (used for polling) */
    getStatus: (videoId: number) =>
      fetcher<VideoMeta>(`/videos/${videoId}`),

    /** DELETE /videos/{id} — Delete a video */
    delete: (videoId: number) =>
      fetcher<void>(`/videos/${videoId}`, { method: "DELETE" }),
  };
}

/**
 * URL helpers for native browser elements (<video>, <img>).
 * These point to Next.js Route Handlers that proxy to FastAPI.
 * NOT part of the fetcher system — these return URL strings, not data.
 */
export function getVideoStreamUrl(videoId: number): string {
  return `/api/videos/${videoId}/stream`;
}

export function getVideoThumbnailUrl(videoId: number): string {
  return `/api/videos/${videoId}/thumbnail`;
}
