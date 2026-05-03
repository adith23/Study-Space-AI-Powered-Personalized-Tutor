import React, { useState } from "react";
import { GalleryVerticalEnd } from "lucide-react"; // Using this as icon for flashcards
import Modal from "@/components/ui/Modal";
import PillButton from "@/components/ui/PillButton";

interface CustomizeFlashcardsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (config: {
    questionCount: "Fewer" | "Standard" | "More";
    difficulty: "Easy" | "Medium" | "Hard";
    focus: string;
  }) => void;
}

const CustomizeFlashcardsModal: React.FC<CustomizeFlashcardsModalProps> = ({ isOpen, onClose, onCreate }) => {
  const [questionCount, setQuestionCount] = useState<"Fewer" | "Standard" | "More">("Standard");
  const [difficulty, setDifficulty] = useState<"Easy" | "Medium" | "Hard">("Medium");
  const [focus, setFocus] = useState("");

  const handleCreate = () => {
    onCreate({ questionCount, difficulty, focus });
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-zinc-700 bg-zinc-800 text-white">
            <GalleryVerticalEnd size={18} className="rotate-90" />
          </div>
          <span>Customize Flashcards</span>
        </div>
      }
    >
      <div className="space-y-8">
        <div className="grid grid-cols-2 gap-8">
          {/* Number of Questions */}
          <div className="space-y-4">
            <h3 className="text-xl text-white">Number of questions</h3>
            <div className="flex gap-3">
              {(["Fewer", "Standard", "More"] as const).map((opt) => (
                <PillButton
                  key={opt}
                  label={opt}
                  isActive={questionCount === opt}
                  onClick={() => setQuestionCount(opt)}
                />
              ))}
            </div>
          </div>

          {/* Level of Difficulty */}
          <div className="space-y-4">
            <h3 className="text-xl text-white">Level of difficulty</h3>
            <div className="flex gap-3">
              {(["Easy", "Medium", "Hard"] as const).map((opt) => (
                <PillButton
                  key={opt}
                  label={opt}
                  isActive={difficulty === opt}
                  onClick={() => setDifficulty(opt)}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Focus Area */}
        <div className="space-y-4">
          <h3 className="text-xl text-white">What should quiz focus on?</h3>
          <textarea
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            className="w-full h-32 resize-none rounded-3xl border border-zinc-700 bg-transparent p-4 text-white focus:border-zinc-500 focus:outline-none"
            placeholder=""
          />
        </div>

        {/* Create Button */}
        <div className="flex justify-end pt-4">
          <button
            onClick={handleCreate}
            className="rounded-full bg-zinc-700 px-8 py-2.5 text-sm font-bold text-white hover:bg-zinc-600 transition-colors"
          >
            Create
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default CustomizeFlashcardsModal;
