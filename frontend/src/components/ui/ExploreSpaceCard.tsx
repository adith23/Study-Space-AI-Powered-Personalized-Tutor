"use client";

import React from "react";
import { LayoutGrid, ArrowRight } from "lucide-react";

interface ExploreSpaceCardProps {
  title: string;
  contentsCount: number;
  onClick?: () => void;
}

export default function ExploreSpaceCard({
  title = "Linear Algebra",
  contentsCount = 12,
  onClick,
}: ExploreSpaceCardProps) {
  return (
    <div
      onClick={onClick}
      className="group relative flex flex-col w-full h-40 bg-black border border-zinc-800/80 rounded-2xl overflow-hidden cursor-pointer select-none hover:border-zinc-700 transition-all duration-300 transform hover:-translate-y-0.5"
    >
      {/* Top Section (Black Background) */}
      <div className="flex-[3] bg-black p-4 flex flex-col justify-end gap-1.5 relative">
        {/* Layout Grid Icon */}
        <LayoutGrid 
          size={16} 
          className="text-zinc-400 group-hover:text-[#00c875] transition-colors duration-300" 
        />
        {/* Title */}
        <h4 className="text-white text-[13px] font-medium tracking-wide leading-tight">
          {title}
        </h4>
        
        {/* Subtle Arrow pointing to explore space (appears on hover) */}
        <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <ArrowRight size={14} className="text-[#00c875]" />
        </div>
      </div>

      {/* Bottom Section (Dark Grey Background) */}
      <div className="flex-[2] bg-[#343436] px-4 py-3 flex items-center justify-between border-t border-zinc-800/40">
        <span className="text-[10px] font-medium text-zinc-400 tracking-wide">
          {contentsCount} Contents
        </span>
        <span className="text-[9px] font-semibold text-[#00c875] opacity-0 group-hover:opacity-100 transition-opacity duration-300 uppercase tracking-wider">
          Explore
        </span>
      </div>
    </div>
  );
}
