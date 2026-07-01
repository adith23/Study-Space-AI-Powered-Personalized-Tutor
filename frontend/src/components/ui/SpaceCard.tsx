"use client";

import React from "react";
import { LayoutGrid } from "lucide-react";

interface SpaceCardProps {
  title: string;
  contentsCount: number;
  onClick?: () => void;
}

export default function SpaceCard({
  title = "Linear Algebra",
  contentsCount = 12,
  onClick,
}: SpaceCardProps) {
  return (
    <div
      onClick={onClick}
      className="group relative flex flex-col w-full h-40 bg-[#343436] border border-white rounded-3xl overflow-hidden cursor-pointer select-none hover:border-[#00c875]/80 transition-all duration-300 transform hover:-translate-y-0.5 hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)]"
    >
      {/* Top Section (Black Background) */}
      <div className="flex-[3] bg-black p-5 pt-12 pb-5 flex flex-col rounded-3xl justify-end gap-1.5">
        {/* Layout Grid Icon */}
        <LayoutGrid
          size={16}
          className="text-zinc-400 group-hover:text-[#00c875] transition-colors duration-300"
        />
        {/* Title */}
        <h4 className="text-white text-[14px] mb-[-8] font-base tracking-wide leading-tight group-hover:text-zinc-100 transition-colors duration-200">
          {title}
        </h4>
      </div>

      {/* Bottom Section (Dark Grey Background) */}
      <div className="flex-[2] bg-[#343436] px-4 py-3 flex items-center">
        <span className="text-[11px] -mt-7 pl-1.5 font-medium text-zinc-400 tracking-wide">
          {contentsCount} Contents
        </span>
      </div>

      {/* Subtle Glow Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
    </div>
  );
}
