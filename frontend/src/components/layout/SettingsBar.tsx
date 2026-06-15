"use client";

import React from "react";
import { SlidersHorizontal } from "lucide-react";

interface SettingsBarProps {
  userName?: string;
  avatarLetter?: string;
  onSettingsClick?: () => void;
}

export default function SettingsBar({
  userName = "Adithya Rusith",
  avatarLetter = "A",
  onSettingsClick,
}: SettingsBarProps) {
  return (
    <div className="flex items-center justify-between bg-black border border-zinc-800/60 rounded-xl px-4 py-3 w-full hover:border-zinc-700 transition-colors duration-200">
      <div className="flex items-center gap-3">
        {/* Green Avatar Icon */}
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[#00c875] text-black font-semibold text-sm select-none">
          {avatarLetter}
        </div>
        
        {/* User Name */}
        <span className="text-zinc-200 text-sm font-medium tracking-wide">
          {userName}
        </span>
      </div>

      {/* Settings Adjust/Slider Button */}
      <button
        onClick={onSettingsClick}
        className="text-zinc-400 hover:text-white transition-colors p-1 rounded-md hover:bg-zinc-800/40"
        aria-label="Settings"
      >
        <SlidersHorizontal size={18} strokeWidth={2} />
      </button>
    </div>
  );
}
