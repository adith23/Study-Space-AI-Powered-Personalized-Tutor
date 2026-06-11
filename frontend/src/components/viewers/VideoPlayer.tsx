import React from "react";
import { Loader2, AlertCircle, Film } from "lucide-react";
import { getVideoStreamUrl } from "@/lib/api/video";
import {
  formatVideoDuration,
  getVideoErrorSummary,
  getVideoRendererLabel,
  VIDEO_STATUS_LABELS,
} from "@/lib/videoPresentation";
import type { VideoMeta, VideoStatusType } from "@/types/video";

interface VideoPlayerProps {
  videoMeta: VideoMeta | null;
}

const STATUS_LABELS: Record<VideoStatusType, string> = {
  pending: `${VIDEO_STATUS_LABELS.pending}...`,
  scripting: `${VIDEO_STATUS_LABELS.scripting}...`,
  generating_code: `${VIDEO_STATUS_LABELS.generating_code}...`,
  planning_visuals: `${VIDEO_STATUS_LABELS.planning_visuals}...`,
  compiling_manim: `${VIDEO_STATUS_LABELS.compiling_manim}...`,
  rendering_manim: `${VIDEO_STATUS_LABELS.rendering_manim}...`,
  generating_images: `${VIDEO_STATUS_LABELS.generating_images}...`,
  generating_audio: `${VIDEO_STATUS_LABELS.generating_audio}...`,
  assembling: `${VIDEO_STATUS_LABELS.assembling}...`,
  completed: VIDEO_STATUS_LABELS.completed,
  failed: VIDEO_STATUS_LABELS.failed,
};

const VideoPlayer: React.FC<VideoPlayerProps> = ({ videoMeta }) => {
  if (!videoMeta) {
    return (
      <div className="flex h-full items-center justify-center text-zinc-500">
        <div className="space-y-3 text-center">
          <Film size={48} className="mx-auto opacity-40" />
          <p>Select a video to preview</p>
        </div>
      </div>
    );
  }

  if (videoMeta.status === "completed" && videoMeta.video_url) {
    return (
      <div className="flex h-full flex-col">
        {videoMeta.title && (
          <div className="border-b border-zinc-800 px-4 py-3">
            <h3 className="truncate text-lg font-semibold text-white">
              {videoMeta.title}
            </h3>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
              {videoMeta.duration_seconds && (
                <span>{formatVideoDuration(videoMeta.duration_seconds)}</span>
              )}
              <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-[10px] uppercase tracking-wide text-zinc-300">
                {getVideoRendererLabel(videoMeta.renderer)}
              </span>
            </div>
          </div>
        )}

        <div className="flex flex-1 items-center justify-center overflow-hidden rounded-b-2xl bg-black">
          <video
            key={videoMeta.id}
            controls
            autoPlay={false}
            className="h-full w-full object-contain"
            src={getVideoStreamUrl(videoMeta.id)}
          >
            Your browser does not support the video tag.
          </video>
        </div>
      </div>
    );
  }

  if (videoMeta.status === "failed") {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="max-w-md space-y-3 px-4 text-center">
          <AlertCircle size={48} className="mx-auto text-red-400" />
          <h3 className="text-lg font-semibold text-white">
            Video Generation Failed
          </h3>
          <p className="text-sm text-zinc-400">
            {getVideoErrorSummary(videoMeta.error_message)}
          </p>
          <div className="flex justify-center">
            <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-[10px] uppercase tracking-wide text-zinc-300">
              {getVideoRendererLabel(videoMeta.renderer)}
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full items-center justify-center">
      <div className="max-w-sm space-y-6 px-4 text-center">
        <Loader2 size={48} className="mx-auto animate-spin text-zinc-400" />

        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-white">
            {STATUS_LABELS[videoMeta.status] || "Processing..."}
          </h3>
          <div className="flex flex-wrap items-center justify-center gap-2 text-sm text-zinc-500">
            {videoMeta.title && <p className="truncate">{videoMeta.title}</p>}
            <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-[10px] uppercase tracking-wide text-zinc-300">
              {getVideoRendererLabel(videoMeta.renderer)}
            </span>
          </div>
        </div>

        <div className="w-full">
          <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-violet-500 transition-all duration-700 ease-out"
              style={{ width: `${videoMeta.progress_pct}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-zinc-500">
            {videoMeta.progress_pct}% complete
          </p>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;
