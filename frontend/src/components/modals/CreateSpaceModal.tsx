"use client";

import React, { useState } from "react";
import { LayoutGrid, Sparkles } from "lucide-react";
import Modal from "@/components/ui/Modal";

interface CreateSpaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (data: { name: string; description?: string; color?: string; is_public?: boolean }) => void;
  isCreating?: boolean;
}

const PRESET_COLORS = [
  "#00c875",
  "#6366f1",
  "#f43f5e",
  "#f59e0b",
  "#06b6d4",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
];

export default function CreateSpaceModal({
  isOpen,
  onClose,
  onCreate,
  isCreating = false,
}: CreateSpaceModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedColor, setSelectedColor] = useState(PRESET_COLORS[0]);
  const [isPublic, setIsPublic] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    onCreate({
      name: name.trim(),
      description: description.trim() || undefined,
      color: selectedColor,
      is_public: isPublic,
    });

    // Reset form
    setName("");
    setDescription("");
    setSelectedColor(PRESET_COLORS[0]);
    setIsPublic(false);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <>
          <Sparkles size={22} className="text-[#00c875]" />
          Create New Space
        </>
      }
      maxWidth="max-w-lg"
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {/* Space Name */}
        <div className="flex flex-col gap-2">
          <label htmlFor="space-name" className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            Space Name
          </label>
          <input
            id="space-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Linear Algebra, Machine Learning..."
            maxLength={255}
            required
            autoFocus
            className="w-full bg-[#131314] border border-zinc-800 focus:border-[#00c875]/60 rounded-xl py-3 px-4 text-sm text-white placeholder-zinc-600 focus:outline-none transition-colors duration-200"
          />
        </div>

        {/* Description */}
        <div className="flex flex-col gap-2">
          <label htmlFor="space-desc" className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            Description <span className="text-zinc-600 font-normal">(optional)</span>
          </label>
          <textarea
            id="space-desc"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What will you study in this space?"
            rows={3}
            className="w-full bg-[#131314] border border-zinc-800 focus:border-[#00c875]/60 rounded-xl py-3 px-4 text-sm text-white placeholder-zinc-600 focus:outline-none transition-colors duration-200 resize-none"
          />
        </div>

        {/* Color Picker */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            Accent Color
          </span>
          <div className="flex gap-2.5">
            {PRESET_COLORS.map((color) => (
              <button
                key={color}
                type="button"
                onClick={() => setSelectedColor(color)}
                className={`w-8 h-8 rounded-full transition-all duration-200 ${
                  selectedColor === color
                    ? "ring-2 ring-white ring-offset-2 ring-offset-[#09090b] scale-110"
                    : "hover:scale-105 opacity-70 hover:opacity-100"
                }`}
                style={{ backgroundColor: color }}
                aria-label={`Select color ${color}`}
              />
            ))}
          </div>
        </div>

        {/* Public Toggle */}
        <div className="flex items-center justify-between py-2">
          <div className="flex flex-col">
            <span className="text-sm text-white font-medium">Make Public</span>
            <span className="text-xs text-zinc-500">Others can discover and explore this space</span>
          </div>
          <button
            type="button"
            onClick={() => setIsPublic(!isPublic)}
            className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
              isPublic ? "bg-[#00c875]" : "bg-zinc-700"
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform duration-200 ${
                isPublic ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        {/* Preview */}
        <div className="bg-[#131314] border border-zinc-800/60 rounded-2xl p-4 flex items-center gap-4">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: `${selectedColor}20` }}
          >
            <LayoutGrid size={20} style={{ color: selectedColor }} />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-white">
              {name.trim() || "Your Space Name"}
            </span>
            <span className="text-xs text-zinc-500">0 Contents</span>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={!name.trim() || isCreating}
          className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed bg-[#00c875] hover:bg-[#00b368] text-black active:scale-[0.98]"
        >
          {isCreating ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
              Creating...
            </span>
          ) : (
            "Create Space"
          )}
        </button>
      </form>
    </Modal>
  );
}
