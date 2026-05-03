import React, { useState } from "react";
import { Video } from "lucide-react";
import Modal from "@/components/ui/Modal";
import PillButton from "@/components/ui/PillButton";

interface VideoStudioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (config: {
    style: "explainer" | "summary" | "deep_dive";
    focus: string;
  }) => void;
}

const VideoStudioModal: React.FC<VideoStudioModalProps> = ({
  isOpen,
  onClose,
  onCreate,
}) => {
  const [style, setStyle] = useState<"explainer" | "summary" | "deep_dive">(
    "explainer"
  );
  const [focus, setFocus] = useState("");

  const handleCreate = () => {
    onCreate({ style, focus });
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
      <div className="space-y-8">
        {/* Video Style */}
        <div className="space-y-4">
          <h3 className="text-xl text-white">Video style</h3>
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

        {/* Focus Area */}
        <div className="space-y-4">
          <h3 className="text-xl text-white">
            What should the video focus on?
          </h3>
          <textarea
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            className="w-full h-32 resize-none rounded-3xl border border-zinc-700 bg-transparent p-4 text-white focus:border-zinc-500 focus:outline-none"
            placeholder="Leave empty to cover the material broadly..."
          />
        </div>

        {/* Info */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4">
          <p className="text-sm text-zinc-400">
            ⏱ The video will be approximately <strong className="text-zinc-300">3 minutes</strong> long
            with 8–12 illustrated scenes narrated by AI. Generation
            typically takes 2–5 minutes.
          </p>
        </div>

        {/* Create Button */}
        <div className="flex justify-end pt-4">
          <button
            onClick={handleCreate}
            className="rounded-full bg-zinc-700 px-8 py-2.5 text-sm font-bold text-white hover:bg-zinc-600 transition-colors"
          >
            Generate Video
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default VideoStudioModal;
