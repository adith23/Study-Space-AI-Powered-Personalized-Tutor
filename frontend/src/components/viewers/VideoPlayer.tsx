import React from "react";
import { Play, Loader2, AlertCircle, Film } from "lucide-react";
import { getVideoStreamUrl } from "@/lib/api/video";
import type { VideoMeta, VideoStatusType } from "@/types/video";

interface VideoPlayerProps {
  videoMeta: VideoMeta | null;
}

const STATUS_LABELS: Record<VideoStatusType, string> = {
  pending: "Preparing...",
  scripting: "Writing script...",
  generating_images: "Generating illustrations...",
  generating_audio: "Creating narration...",
  assembling: "Assembling video...",
  completed: "Complete",
  failed: "Failed",
};

const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoMeta }) => {
  if (!videoMeta) {
    return (
      <div className="flex h-full items-center justify-center text-zinc-500">
        <div className="text-center space-y-3">
          <Film size={48} className="mx-auto opacity-40" />
          <p>Select a video to preview</p>
        </div>
      </div>
    );
  }

  // ── Completed — Show video player ───────────────────────────────────
  if (videoMeta.status === "completed" && videoMeta.video_url) {
    return (
      <div className="flex flex-col h-full">
        {/* Title */}
        {videoMeta.title && (
          <div className="px-4 py-3 border-b border-zinc-800">
            <h3 className="text-lg font-semibold text-white truncate">
              {videoMeta.title}
            </h3>
            {videoMeta.duration_seconds && (
              <p className="text-xs text-zinc-500 mt-1">
                {Math.floor(videoMeta.duration_seconds / 60)}:
                {String(Math.floor(videoMeta.duration_seconds % 60)).padStart(2, "0")}
              </p>
            )}
          </div>
        )}

        {/* Player */}
        <div className="flex-1 flex items-center justify-center bg-black rounded-b-2xl overflow-hidden">
          <video
            key={videoMeta.id}
            controls
            autoPlay={false}
            className="w-full h-full object-contain"
            src={getVideoStreamUrl(videoMeta.id)}
          >
            Your browser does not support the video tag.
          </video>
        </div>
      </div>
    );
  }

  // ── Failed — Show error ─────────────────────────────────────────────
  if (videoMeta.status === "failed") {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-3 max-w-md px-4">
          <AlertCircle size={48} className="mx-auto text-red-400" />
          <h3 className="text-lg font-semibold text-white">
            Video Generation Failed
          </h3>
          <p className="text-sm text-zinc-400">
            {videoMeta.error_message || "An unexpected error occurred."}
          </p>
        </div>
      </div>
    );
  }

  // ── In Progress — Show progress ─────────────────────────────────────
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center space-y-6 max-w-sm px-4">
        <Loader2 size={48} className="mx-auto text-zinc-400 animate-spin" />

        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-white">
            {STATUS_LABELS[videoMeta.status] || "Processing..."}
          </h3>
          {videoMeta.title && (
            <p className="text-sm text-zinc-500 truncate">{videoMeta.title}</p>
          )}
        </div>

        {/* Progress bar */}
        <div className="w-full">
          <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-violet-500 transition-all duration-700 ease-out"
              style={{ width: `${videoMeta.progress_pct}%` }}
            />
          </div>
          <p className="text-xs text-zinc-500 mt-2">
            {videoMeta.progress_pct}% complete
          </p>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;
