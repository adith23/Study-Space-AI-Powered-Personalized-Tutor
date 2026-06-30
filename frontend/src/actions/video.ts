"use server";

import { api } from "@/lib/api/index.server";
import { isNextRedirectError } from "@/lib/api/transport.server";
import type { VideoGenerateRequest } from "@/types/video";

export async function generateVideoAction(spaceId: number, payload: VideoGenerateRequest) {
  return api.spaces.generateVideo(spaceId, payload);
}

export async function deleteVideoAction(videoId: number) {
  try {
    await api.video.delete(videoId);
    return { error: null };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return { error: err instanceof Error ? err.message : "Delete failed" };
  }
}
