import { useState, useEffect, useCallback, useRef } from "react";
import {
  generateVideo,
  getVideoStatus,
  listVideos,
  deleteVideo,
} from "@/lib/api/video";
import type {
  VideoListItem,
  VideoMeta,
  VideoStatusType,
} from "@/types/video";

const POLL_INTERVAL_MS = 2000;

const TERMINAL_STATUSES: VideoStatusType[] = ["completed", "failed"];

export function useVideoGeneration(selectedFileIds: Set<number>) {
  const [videos, setVideos] = useState<VideoListItem[]>([]);
  const [activeVideoId, setActiveVideoId] = useState<number | null>(null);
  const [activeVideoMeta, setActiveVideoMeta] = useState<VideoMeta | null>(
    null
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Fetch the list of videos on mount
  useEffect(() => {
    listVideos()
      .then(setVideos)
      .catch((err) => console.error("Failed to fetch videos:", err));
  }, []);

  // Poll the active video's status
  useEffect(() => {
    if (!activeVideoId) return;

    const poll = async () => {
      try {
        const meta = await getVideoStatus(activeVideoId);
        setActiveVideoMeta(meta);

        if (TERMINAL_STATUSES.includes(meta.status)) {
          // Stop polling
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
          setIsGenerating(false);

          // Update the list entry
          setVideos((prev) =>
            prev.map((v) =>
              v.id === activeVideoId
                ? {
                    ...v,
                    status: meta.status,
                    title: meta.title ?? v.title,
                    duration_seconds:
                      meta.duration_seconds ?? v.duration_seconds,
                  }
                : v
            )
          );
        }
      } catch (err) {
        console.error("Failed to poll video status:", err);
      }
    };

    // Immediate first poll
    poll();
    pollRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [activeVideoId]);

  const handleGenerateVideo = useCallback(
    async (config: {
      style: "explainer" | "summary" | "deep_dive";
      focus: string;
    }) => {
      const fileIds = Array.from(selectedFileIds);
      if (fileIds.length === 0) {
        alert("Select at least one processed source for video generation.");
        return;
      }

      try {
        setIsGenerating(true);
        const result = await generateVideo({
          file_ids: fileIds,
          style: config.style,
          focus_prompt: config.focus.trim() || null,
        });

        // Add to list
        const newItem: VideoListItem = {
          id: result.id,
          status: result.status as VideoStatusType,
          created_at: new Date().toISOString(),
        };
        setVideos((prev) => [newItem, ...prev]);
        setActiveVideoId(result.id);
        setActiveVideoMeta(null);
      } catch (err) {
        console.error("Failed to start video generation:", err);
        alert("Failed to start video generation.");
        setIsGenerating(false);
      }
    },
    [selectedFileIds]
  );

  const handleDeleteVideo = useCallback(
    async (videoId: number) => {
      try {
        await deleteVideo(videoId);
        setVideos((prev) => prev.filter((v) => v.id !== videoId));
        if (activeVideoId === videoId) {
          setActiveVideoId(null);
          setActiveVideoMeta(null);
        }
      } catch (err) {
        console.error("Failed to delete video:", err);
      }
    },
    [activeVideoId]
  );

  return {
    videos,
    activeVideoId,
    setActiveVideoId,
    activeVideoMeta,
    isGenerating,
    handleGenerateVideo,
    handleDeleteVideo,
  };
}
