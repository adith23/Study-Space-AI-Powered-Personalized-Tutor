export default function SpaceLoading() {
  return (
    <div className="flex flex-col h-screen bg-black text-white font-sans overflow-hidden">
      {/* Top nav skeleton */}
      <div className="h-12 bg-[#131314] border-b border-zinc-800/40 flex items-center px-4">
        <div className="h-4 w-40 bg-zinc-800 rounded animate-pulse" />
      </div>

      <div className="flex flex-grow min-h-0">
        {/* Content panel skeleton */}
        <div className="w-72 bg-[#131314] border-r border-zinc-800/40 p-4 flex flex-col gap-3">
          <div className="h-8 w-full bg-zinc-800/60 rounded-lg animate-pulse" />
          <div className="h-8 w-full bg-zinc-800/60 rounded-lg animate-pulse" />
          <div className="h-8 w-3/4 bg-zinc-800/60 rounded-lg animate-pulse" />
        </div>

        {/* Main content skeleton */}
        <main className="flex-grow flex items-center justify-center bg-[#09090b]">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-zinc-600 border-t-[#00c875] rounded-full animate-spin" />
            <span className="text-zinc-500 text-sm">Loading space...</span>
          </div>
        </main>

        {/* AI panel skeleton */}
        <div className="w-80 bg-[#131314] border-l border-zinc-800/40 p-4 flex flex-col gap-3">
          <div className="h-8 w-full bg-zinc-800/60 rounded-lg animate-pulse" />
          <div className="h-32 w-full bg-zinc-800/60 rounded-lg animate-pulse" />
          <div className="h-8 w-2/3 bg-zinc-800/60 rounded-lg animate-pulse" />
        </div>
      </div>
    </div>
  );
}
