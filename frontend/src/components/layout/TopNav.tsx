import React from "react";
import { Settings, Share2, Menu, User } from "lucide-react";

interface TopNavProps {
  title: string;
}

const TopNav: React.FC<TopNavProps> = ({ title }) => {
  return (
    <header className="flex h-16 items-center justify-between border-b border-zinc-800 bg-black px-6 text-white shrink-0">
      <div className="flex items-center gap-3 w-1/3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-800">
          <div className="h-5 w-5 rounded-full border-2 border-white opacity-80" style={{ borderTopColor: 'transparent', transform: 'rotate(45deg)' }} />
        </div>
        <span className="text-lg font-bold tracking-tight">Study Space</span>
      </div>

      <div className="flex justify-center w-1/3">
        <h1 className="text-lg font-medium text-zinc-200 truncate">{title}</h1>
      </div>

      <div className="flex items-center justify-end gap-3 w-1/3">
        <button className="flex items-center gap-2 rounded-full border border-zinc-700 bg-zinc-900/50 px-4 py-1.5 text-sm font-medium text-zinc-300 hover:bg-zinc-800 transition-colors">
          <Share2 size={16} />
          Share
        </button>
        <button className="flex items-center gap-2 rounded-full border border-zinc-700 bg-zinc-900/50 px-4 py-1.5 text-sm font-medium text-zinc-300 hover:bg-zinc-800 transition-colors">
          <Settings size={16} />
          Setting
        </button>
        <div className="h-6 w-px bg-zinc-700 mx-2" />
        <button className="p-2 text-zinc-400 hover:text-white transition-colors">
          <Menu size={24} />
        </button>
        <button className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-white hover:bg-blue-700 transition-colors">
          <User size={18} />
        </button>
      </div>
    </header>
  );
};

export default TopNav;
