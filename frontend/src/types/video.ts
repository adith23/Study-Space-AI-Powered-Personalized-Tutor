export type VideoRendererType = "image" | "manim";

export type VideoStatusType =
  | "pending"
  | "scripting"
  | "planning_visuals"
  | "compiling_manim"
  | "rendering_manim"
  | "generating_images"
  | "generating_audio"
  | "assembling"
  | "completed"
  | "failed";

export interface VideoGenerateRequest {
  file_ids: number[];
  focus_prompt?: string | null;
  style?: "explainer" | "summary" | "deep_dive";
  renderer?: VideoRendererType;
}

export interface VideoGenerateResponse {
  id: number;
  status: string;
  renderer?: VideoRendererType | null;
}

export interface VideoMeta {
  id: number;
  status: VideoStatusType;
  progress_pct: number;
  title?: string | null;
  duration_seconds?: number | null;
  video_url?: string | null;
  thumbnail_url?: string | null;
  created_at?: string | null;
  error_message?: string | null;
  style?: string | null;
  renderer?: VideoRendererType | null;
}

export interface VideoListItem {
  id: number;
  title?: string | null;
  status: VideoStatusType;
  duration_seconds?: number | null;
  style?: string | null;
  created_at?: string | null;
  renderer?: VideoRendererType | null;
}
