"use client";

import React from "react";
import { Plus } from "lucide-react";

interface AddSpaceCardProps {
  onClick?: () => void;
}

export default function AddSpaceCard({ onClick }: AddSpaceCardProps) {
  return (
    <div
      onClick={onClick}
      className="group flex flex-col items-center justify-center w-full h-40 bg-transparent border-1 border-dashed border-white rounded-3xl cursor-pointer select-none hover:border-[#00c875]/80 hover:bg-[#00c875]/[0.02] transition-all duration-300 transform hover:-translate-y-0.5"
    >
      <div className="flex flex-col items-center gap-2">
        {/* Plus Icon with hover rotation */}
        <div className="flex items-center justify-center p-2 rounded-full bg-zinc-900/60 group-hover:bg-zinc-800 group-hover:scale-110 transition-all duration-300">
          <Plus
            size={40}
            className="text-white group-hover:text-[#00c875] transition-colors duration-300"
            strokeWidth={2.5}
          />
        </div>

        {/* Text */}
        <span className="text-white text-[17px] font-normal tracking-wide leading-tight group-hover:text-zinc-200 transition-colors duration-200">
          New Space
        </span>
      </div>
    </div>
  );
}
