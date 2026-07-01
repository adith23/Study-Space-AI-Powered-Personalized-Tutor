"use server";

import { api } from "@/lib/api/index.server";
import { isNextRedirectError } from "@/lib/api/transport.server";
import type { VideoGenerateRequest } from "@/types/video";
import type { ActionResult } from "@/types";

export async function generateVideoAction(
  spaceId: number,
  payload: VideoGenerateRequest,
): Promise<ActionResult<any>> {
  try {
    const data = await api.spaces.generateVideo(spaceId, payload);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to generate video",
      data: null,
    };
  }
}

export async function deleteVideoAction(videoId: number): Promise<ActionResult<void>> {
  try {
    await api.video.delete(videoId);
    return { error: null, data: null };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to delete video",
      data: null,
    };
  }
}
