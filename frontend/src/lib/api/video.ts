import { api } from "./client";
import type {
  VideoGenerateRequest,
  VideoGenerateResponse,
  VideoListItem,
  VideoMeta,
} from "@/types/video";

export async function generateVideo(payload: VideoGenerateRequest) {
  const response = await api.post<VideoGenerateResponse>(
    "/videos/generate",
    payload
  );
  return response.data;
}

export async function listVideos() {
  const response = await api.get<VideoListItem[]>("/videos");
  return response.data;
}

export async function getVideoStatus(videoId: number) {
  const response = await api.get<VideoMeta>(`/videos/${videoId}`);
  return response.data;
}

export async function deleteVideo(videoId: number) {
  await api.delete(`/videos/${videoId}`);
}

/**
 * Returns the URL to stream/download the generated video.
 * This URL can be used directly in a <video> element's src attribute.
 */
export function getVideoStreamUrl(videoId: number): string {
  return `/api/v1/videos/${videoId}/stream`;
}

export function getVideoThumbnailUrl(videoId: number): string {
  return `/api/v1/videos/${videoId}/thumbnail`;
}
