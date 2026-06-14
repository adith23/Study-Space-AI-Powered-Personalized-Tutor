"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Upload, Link as LinkIcon, Clipboard, Search } from "lucide-react";

// Components
import LeftSidebar from "@/components/layout/LeftSidebar";
import SpaceCard from "@/components/ui/SpaceCard";
import AddSpaceCard from "@/components/ui/AddSpaceCard";
import ExploreSpaceCard from "@/components/ui/ExploreSpaceCard";
import CreateSpaceModal from "@/components/modals/CreateSpaceModal";

// Actions
import {
  listSpacesAction,
  createSpaceAction,
  exploreSpacesAction,
} from "@/actions/spaces";

// Types
import type { SpaceListItem, ExploreSpaceItem } from "@/types/space";

export default function Home() {
  const router = useRouter();
  const [currentPath, setCurrentPath] = useState("home");
  const [exploreQuery, setExploreQuery] = useState("");
  const [spacesQuery, setSpacesQuery] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // Real space data
  const [recentSpaces, setRecentSpaces] = useState<SpaceListItem[]>([]);
  const [exploreSpaces, setExploreSpaces] = useState<ExploreSpaceItem[]>([]);
  const [activeSpaceId, setActiveSpaceId] = useState<number | null>(null);

  // Fetch user's spaces on mount
  useEffect(() => {
    (async () => {
      const result = await listSpacesAction();
      if (result.data) {
        setRecentSpaces(result.data);
      }
    })();
  }, []);

  // Fetch explore spaces on mount
  useEffect(() => {
    (async () => {
      const result = await exploreSpacesAction();
      if (result.data) {
        setExploreSpaces(result.data);
      }
    })();
  }, []);

  // Search explore spaces
  useEffect(() => {
    const timer = setTimeout(async () => {
      const result = await exploreSpacesAction(spacesQuery || undefined);
      if (result.data) {
        setExploreSpaces(result.data);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [spacesQuery]);

  // Handle sidebar navigation
  const handleNavigate = (path: string) => {
    setCurrentPath(path);
    if (path === "new-space") {
      setIsCreateModalOpen(true);
    }
  };

  // Handle space selection in sidebar
  const handleSpaceSelect = (spaceId: string) => {
    const numericId = parseInt(spaceId, 10);
    setActiveSpaceId(numericId);
    router.push(`/spaces/${numericId}`);
  };

  // Handle space card click
  const handleSpaceClick = (spaceId: number) => {
    router.push(`/spaces/${spaceId}`);
  };

  // Handle creating a new space
  const handleCreateSpace = async (data: {
    name: string;
    description?: string;
    color?: string;
    is_public?: boolean;
  }) => {
    setIsCreating(true);
    try {
      const result = await createSpaceAction(data);
      if (result.data) {
        setIsCreateModalOpen(false);
        // Navigate to the new space
        router.push(`/spaces/${result.data.id}`);
      }
    } catch (error) {
      console.error("Failed to create space", error);
    } finally {
      setIsCreating(false);
    }
  };

  // Map spaces to sidebar format
  const sidebarSpaces = recentSpaces.slice(0, 5).map((space) => ({
    id: String(space.id),
    name: space.name,
    isActive: space.id === activeSpaceId,
  }));

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-black text-white font-sans">
      {/* Left Sidebar Navigation */}
      <LeftSidebar
        currentPath={currentPath}
        recentSpaces={sidebarSpaces}
        onNavigate={handleNavigate}
        onSpaceSelect={handleSpaceSelect}
      />

      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-y-auto bg-black flex flex-col px-8 md:px-12 py-6 relative">
        {/* Top Header - Upgrade Button */}
        <div className="flex justify-end items-center mb-10 w-full">
          <button className="border border-[#00c875] text-[#00c875] bg-[#00c875]/[0.02] hover:bg-[#00c875]/10 text-xs font-semibold px-6 py-2.5 rounded-full transition-all duration-300 transform active:scale-95 shadow-[0_0_15px_rgba(0,200,117,0.1)]">
            Upgrade
          </button>
        </div>

        {/* Central Hub Container (Welcome & Short Actions) */}
        <div className="max-w-4xl mx-auto w-full mb-12 flex flex-col items-center">
          {/* Greeting */}
          <h2 className="text-zinc-100 text-2xl md:text-[28px] font-base text-center mb-8 tracking-wide">
            Hey Adithya, ready to learn?
          </h2>

          {/* Quick Action Cards (Upload, Link, Paste) */}
          <div className="grid grid-cols-3 gap-4 w-full max-w-lg mb-8">
            {/* Upload Card */}
            <button className="group flex flex-col items-start bg-[#202022] hover:bg-[#28282b] border border-zinc-800/40 rounded-xl p-4 text-left transition-all duration-200 hover:-translate-y-0.5">
              <div className="p-1.5 rounded-lg bg-zinc-900 group-hover:bg-zinc-850 text-zinc-300 group-hover:text-white transition-all mb-3.5">
                <Upload size={16} />
              </div>
              <span className="text-white text-xs font-semibold block mb-0.5">
                Upload
              </span>
              <span className="text-zinc-500 text-[9px] font-medium leading-normal">
                Files, Audio, Video
              </span>
            </button>

            {/* Link Card */}
            <button className="group flex flex-col items-start bg-[#202022] hover:bg-[#28282b] border border-zinc-800/40 rounded-xl p-4 text-left transition-all duration-200 hover:-translate-y-0.5">
              <div className="p-1.5 rounded-lg bg-zinc-900 group-hover:bg-zinc-850 text-zinc-300 group-hover:text-white transition-all mb-3.5">
                <LinkIcon size={16} />
              </div>
              <span className="text-white text-xs font-semibold block mb-0.5">
                Link
              </span>
              <span className="text-zinc-500 text-[9px] font-medium leading-normal">
                YouTube, Website
              </span>
            </button>

            {/* Paste Card */}
            <button className="group flex flex-col items-start bg-[#202022] hover:bg-[#28282b] border border-zinc-800/40 rounded-xl p-4 text-left transition-all duration-200 hover:-translate-y-0.5">
              <div className="p-1.5 rounded-lg bg-zinc-900 group-hover:bg-zinc-850 text-zinc-300 group-hover:text-white transition-all mb-3.5">
                <Clipboard size={16} />
              </div>
              <span className="text-white text-xs font-semibold block mb-0.5">
                Paste
              </span>
              <span className="text-zinc-500 text-[9px] font-medium leading-normal">
                Copied Text
              </span>
            </button>
          </div>

          {/* Central Search Pill */}
          <div className="w-full max-w-lg relative">
            <input
              type="text"
              placeholder="Explore Anything"
              value={exploreQuery}
              onChange={(e) => setExploreQuery(e.target.value)}
              className="w-full bg-black border border-zinc-800 focus:border-zinc-650 hover:border-zinc-700/80 rounded-full py-2.5 pl-6 pr-12 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none transition-all duration-300"
            />
            <div className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 pointer-events-none">
              <Search size={16} />
            </div>
          </div>
        </div>

        {/* Recent Spaces Section */}
        <section className="mb-10 w-full max-w-5xl mx-auto">
          <h3 className="text-zinc-200 text-sm font-semibold tracking-wider mb-4">
            Recent Spaces
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {/* Add Space Card */}
            <AddSpaceCard onClick={() => setIsCreateModalOpen(true)} />

            {/* Dynamic Space Cards */}
            {recentSpaces.slice(0, 3).map((space) => (
              <SpaceCard
                key={space.id}
                title={space.name}
                contentsCount={space.content_count}
                onClick={() => handleSpaceClick(space.id)}
              />
            ))}
          </div>
        </section>

        {/* Explore Spaces Section */}
        <section className="w-full max-w-5xl mx-auto mb-12">
          <h3 className="text-zinc-200 text-sm font-semibold tracking-wider mb-3">
            Explore Spaces
          </h3>

          {/* Search and Explore input */}
          <div className="w-full max-w-xs relative mb-5">
            <input
              type="text"
              placeholder="Search and Explore Spaces"
              value={spacesQuery}
              onChange={(e) => setSpacesQuery(e.target.value)}
              className="w-full bg-[#0d0d0e] border border-zinc-850 hover:border-zinc-800 focus:border-zinc-700 rounded-full py-1.5 pl-4 pr-10 text-[10px] text-zinc-300 placeholder-zinc-500 focus:outline-none transition-all duration-200"
            />
            <div className="absolute right-3.5 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none">
              <Search size={12} />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {exploreSpaces.length > 0 ? (
              exploreSpaces.map((space) => (
                <ExploreSpaceCard
                  key={space.id}
                  title={space.name}
                  contentsCount={space.content_count}
                />
              ))
            ) : (
              <div className="col-span-3 py-8 text-center text-zinc-600 text-xs">
                {spacesQuery
                  ? "No spaces match your search."
                  : "No public spaces available yet."}
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Create Space Modal */}
      <CreateSpaceModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreate={handleCreateSpace}
        isCreating={isCreating}
      />
    </div>
  );
}
