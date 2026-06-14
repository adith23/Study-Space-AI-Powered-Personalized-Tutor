"use client";

import React, { useState } from "react";
import { 
  Home, 
  Search, 
  Plus, 
  LayoutGrid, 
  ChevronsLeft,
  BookOpen
} from "lucide-react";
import SettingsBar from "./SettingsBar";

interface RecentSpaceItem {
  id: string;
  name: string;
  isActive?: boolean;
}

interface LeftSidebarProps {
  currentPath?: string;
  recentSpaces?: RecentSpaceItem[];
  onCollapseToggle?: () => void;
  onNavigate?: (path: string) => void;
  onSpaceSelect?: (spaceId: string) => void;
}

export default function LeftSidebar({
  currentPath = "home",
  recentSpaces = [
    { id: "1", name: "Intermediate Calculus", isActive: true },
    { id: "2", name: "Linear Algebra", isActive: false },
    { id: "3", name: "Intermediate Calculus", isActive: false },
    { id: "4", name: "Intermediate Calculus", isActive: false },
  ],
  onCollapseToggle,
  onNavigate,
  onSpaceSelect,
}: LeftSidebarProps) {
  return (
    <aside className="w-64 h-full bg-[#131314] text-white flex flex-col justify-between p-4 select-none border-r border-zinc-900/60">
      {/* Top Section */}
      <div className="flex flex-col gap-6">
        
        {/* Header Logo */}
        <div className="flex items-center justify-between px-2 pt-2">
          <div className="flex items-center gap-2 cursor-pointer">
            <BookOpen className="text-[#00c875] w-6 h-6" strokeWidth={2.5} />
            <span className="font-semibold text-lg tracking-wide text-zinc-100">Study Space</span>
          </div>
          <button 
            onClick={onCollapseToggle}
            className="text-zinc-500 hover:text-zinc-300 transition-colors p-1 rounded-md hover:bg-zinc-800/40"
            aria-label="Collapse Sidebar"
          >
            <ChevronsLeft size={18} />
          </button>
        </div>

        {/* Primary Navigation Menu */}
        <nav className="flex flex-col gap-1.5 px-1">
          <button
            onClick={() => onNavigate?.("home")}
            className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              currentPath === "home"
                ? "bg-[#202024]/60 text-white font-semibold"
                : "text-zinc-400 hover:text-zinc-100 hover:bg-[#202024]/20"
            }`}
          >
            <Home size={18} />
            <span>Home</span>
          </button>

          <button
            onClick={() => onNavigate?.("search")}
            className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              currentPath === "search"
                ? "bg-[#202024]/60 text-white font-semibold"
                : "text-zinc-400 hover:text-zinc-100 hover:bg-[#202024]/20"
            }`}
          >
            <Search size={18} />
            <span>Search Spaces</span>
          </button>

          <button
            onClick={() => onNavigate?.("new-space")}
            className={`flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              currentPath === "new-space"
                ? "bg-[#202024]/60 text-white font-semibold"
                : "text-zinc-400 hover:text-zinc-100 hover:bg-[#202024]/20"
            }`}
          >
            <Plus size={18} />
            <span>New Space</span>
          </button>
        </nav>

        {/* Recent Spaces Section */}
        <div className="flex flex-col px-1 mt-2">
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-3 mb-2.5">
            Recent Spaces
          </span>
          <div className="flex flex-col gap-1.5">
            {recentSpaces.map((space) => (
              <button
                key={space.id}
                onClick={() => onSpaceSelect?.(space.id)}
                className={`flex items-center gap-3 w-full px-3 py-2 rounded-xl text-xs transition-all ${
                  space.isActive
                    ? "bg-[#1d1d1f] border border-zinc-800/80 text-white font-medium"
                    : "text-zinc-400 border border-transparent hover:text-zinc-100 hover:bg-[#202024]/20"
                }`}
              >
                <LayoutGrid size={15} className={space.isActive ? "text-[#00c875]" : "text-zinc-400"} />
                <span className="truncate">{space.name}</span>
              </button>
            ))}
          </div>
        </div>

      </div>

      {/* Bottom Section */}
      <div className="pt-4 mt-auto">
        <SettingsBar />
      </div>
    </aside>
  );
}
