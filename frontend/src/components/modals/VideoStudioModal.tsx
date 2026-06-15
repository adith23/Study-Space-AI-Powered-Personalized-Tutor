import React, { useState } from "react";
import { Video } from "lucide-react";
import Modal from "@/components/ui/Modal";
import PillButton from "@/components/ui/PillButton";
import type { VideoRendererType } from "@/types/video";

interface VideoStudioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (config: {
    renderer: VideoRendererType;
    style: "explainer" | "summary" | "deep_dive";
    focus: string;
  }) => void;
}

const VideoStudioModal: React.FC<VideoStudioModalProps> = ({
  isOpen,
  onClose,
  onCreate,
}) => {
  const [renderer, setRenderer] = useState<VideoRendererType>("image");
  const [style, setStyle] = useState<"explainer" | "summary" | "deep_dive">(
    "explainer",
  );
  const [focus, setFocus] = useState("");

  const handleCreate = () => {
    onCreate({ renderer, style, focus });
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-zinc-700 bg-zinc-800 text-white">
            <Video size={18} />
          </div>
          <span>Generate Video</span>
        </div>
      }
    >
      <div className="space-y-6">
        <div className="space-y-2.5">
          <h3 className="text-lg font-medium text-white">Renderer</h3>
          <div className="inline-flex rounded-full bg-zinc-900 p-1 ring-1 ring-zinc-800">
            {[
              { value: "image" as const, label: "Classic" },
              { value: "manim" as const, label: "Technical / Manim" },
              { value: "manim_pro" as const, label: "Manim Pro" },
            ].map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setRenderer(option.value)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                  renderer === option.value
                    ? "bg-zinc-700 text-white"
                    : "text-zinc-400 hover:text-white"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
          <p className="text-sm text-zinc-500">
            {renderer === "image" &&
              "Classic uses illustrated scene generation for a broad explainer format."}
            {renderer === "manim" &&
              "Technical / Manim uses predefined animated diagrams, charts, and structured visuals."}
            {renderer === "manim_pro" &&
              "Manim Pro generates advanced custom animations using AI code generation for maximum visual quality."}
          </p>
        </div>

        <div className="space-y-2.5">
          <h3 className="text-lg font-medium text-white">Video style</h3>
          <div className="flex gap-3">
            {(
              [
                { value: "explainer", label: "Explainer" },
                { value: "summary", label: "Summary" },
                { value: "deep_dive", label: "Deep Dive" },
              ] as const
            ).map((opt) => (
              <PillButton
                key={opt.value}
                label={opt.label}
                isActive={style === opt.value}
                onClick={() => setStyle(opt.value)}
              />
            ))}
          </div>
          <p className="text-sm text-zinc-500">
            {style === "explainer" &&
              "A clear, step-by-step walkthrough of the key concepts."}
            {style === "summary" &&
              "A concise overview hitting only the main highlights."}
            {style === "deep_dive" &&
              "An in-depth exploration with nuance and detail."}
          </p>
        </div>

        <div className="space-y-2.5">
          <h3 className="text-lg font-medium text-white">
            What should the video focus on?
          </h3>
          <textarea
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            className="h-24 w-full resize-none rounded-2xl border border-zinc-700 bg-transparent p-3 text-white focus:border-zinc-500 focus:outline-none"
            placeholder={
              renderer === "image"
                ? "Leave empty to cover the material broadly..."
                : renderer === "manim"
                  ? "Mention the concept, formula, chart, process, or technical flow to visualize..."
                  : "Describe the concepts, relationships, or processes you want animated in detail..."
            }
          />
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-3">
          <p className="text-sm text-zinc-400">
            {renderer === "image" && (
              <>
                The video will be approximately{" "}
                <strong className="text-zinc-300">3 minutes</strong> long with
                illustrated scenes narrated by AI. Generation typically takes
                2-5 minutes.
              </>
            )}
            {renderer === "manim" && (
              <>
                The video will be approximately{" "}
                <strong className="text-zinc-300">3 minutes</strong> long with
                technical animated visuals and AI narration. Generation may take
                longer than Classic while the animation is compiled and
                rendered.
              </>
            )}
            {renderer === "manim_pro" && (
              <>
                The video will be approximately{" "}
                <strong className="text-zinc-300">3 minutes</strong> long with
                AI-generated custom Manim animations. Generation may take longer
                due to code generation, validation, and rendering.
              </>
            )}
          </p>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={handleCreate}
            className="rounded-full bg-zinc-700 px-6 py-2 text-sm font-bold text-white transition-colors hover:bg-zinc-600"
          >
            Generate Video
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default VideoStudioModal;
