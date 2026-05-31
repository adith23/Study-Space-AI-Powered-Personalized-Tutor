import type {
  VideoMeta,
  VideoRendererType,
  VideoStatusType,
} from "@/types/video";

export const DEFAULT_VIDEO_RENDERER: VideoRendererType = "image";

export const VIDEO_RENDERER_LABELS: Record<VideoRendererType, string> = {
  image: "Classic",
  manim: "Manim",
};

export const VIDEO_STATUS_LABELS: Record<VideoStatusType, string> = {
  pending: "Preparing",
  scripting: "Writing script",
  planning_visuals: "Planning visuals",
  compiling_manim: "Compiling animation",
  rendering_manim: "Rendering animation",
  generating_images: "Generating illustrations",
  generating_audio: "Creating narration",
  assembling: "Assembling video",
  completed: "Complete",
  failed: "Failed",
};

export function getVideoRenderer(renderer?: VideoRendererType | null): VideoRendererType {
  return renderer ?? DEFAULT_VIDEO_RENDERER;
}

export function getVideoRendererLabel(
  renderer?: VideoRendererType | null
): string {
  return VIDEO_RENDERER_LABELS[getVideoRenderer(renderer)];
}

export function getVideoStatusLabel(status: VideoStatusType): string {
  return VIDEO_STATUS_LABELS[status] ?? "Processing";
}

export function formatVideoDuration(durationSeconds?: number | null): string | null {
  if (!durationSeconds) {
    return null;
  }
  const minutes = Math.floor(durationSeconds / 60);
  const seconds = Math.floor(durationSeconds % 60);
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function getVideoErrorSummary(errorMessage?: string | null): string {
  const raw = errorMessage?.trim();
  if (!raw) {
    return "An unexpected error occurred.";
  }
  const lowered = raw.toLowerCase();
  if (
    lowered.includes("manim runtime") ||
    lowered.includes("manim health") ||
    lowered.includes("latex is unavailable") ||
    lowered.includes("ffmpeg is unavailable")
  ) {
    return "The animation runtime is unavailable for this video job.";
  }
  if (lowered.includes("render failed")) {
    return "The animation could not be rendered successfully.";
  }
  if (lowered.includes("assembly")) {
    return "The final video could not be assembled.";
  }
  return raw;
}

export function formatVideoSubtitle(video: Pick<VideoMeta, "status" | "duration_seconds" | "renderer">): string {
  const rendererLabel = getVideoRendererLabel(video.renderer);
  if (video.status === "completed") {
    const duration = formatVideoDuration(video.duration_seconds);
    return duration ? `${duration} | ${rendererLabel}` : rendererLabel;
  }
  return `${rendererLabel} | ${getVideoStatusLabel(video.status)}`;
}
