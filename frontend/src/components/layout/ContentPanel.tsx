import React, { useState } from "react";
import { ChevronsLeft, Plus, Search, FileText, AlertCircle, X, MoreHorizontal } from "lucide-react";
import type { UploadedFileState } from "@/types/dashboard";

interface ContentPanelProps {
  files: UploadedFileState[];
  selectedFileIds: Set<number>;
  onSelectFile: (id: number) => void;
  onSelectAll: () => void;
  onAddContent: () => void;
  onFileClick: (id: number) => void;
  viewingFileId: number | null;
  onRenameFile: (id: number, newName: string) => Promise<void>;
  onDeleteFile: (id: number) => Promise<void>;
  onDismissFile: (id: number) => Promise<void>;
}

const ContentPanel: React.FC<ContentPanelProps> = ({
  files,
  selectedFileIds,
  onSelectFile,
  onSelectAll,
  onAddContent,
  onFileClick,
  viewingFileId,
  onRenameFile,
  onDeleteFile,
  onDismissFile
}) => {
  const [activeMenuFileId, setActiveMenuFileId] = useState<number | null>(null);
  const [editingFileId, setEditingFileId] = useState<number | null>(null);
  const [editName, setEditName] = useState<string>("");

  const successFiles = files.filter((f) => f.status === "success");
  const allSelected = successFiles.length > 0 && selectedFileIds.size === successFiles.length;

  return (
    <aside className="flex flex-col w-64 bg-[#1e1f22] border-r border-zinc-800 shrink-0">
      <div className="flex items-center justify-between p-4 border-b border-zinc-800">
        <h2 className="text-sm font-semibold text-white">Content</h2>
        <button className="text-zinc-400 hover:text-white transition-colors">
          <ChevronsLeft size={18} />
        </button>
      </div>

      <div className="p-4 space-y-4 flex-grow overflow-y-auto">
        <div className="flex gap-2">
          <button
            onClick={onAddContent}
            className="flex-[1.3] flex items-center justify-center gap-1.5 px-2 py-2 rounded-full border border-zinc-700 bg-transparent text-sm text-zinc-300 hover:text-white hover:bg-zinc-800 transition-colors"
          >
            <Plus size={16} />
            <span className="whitespace-nowrap">Add Content</span>
          </button>
          <button className="flex-1 flex items-center justify-center gap-1.5 px-1 py-2 rounded-full border border-zinc-700 bg-transparent text-sm text-zinc-300 hover:text-white hover:bg-zinc-800 transition-colors">
            <Search size={16} />
            Search
          </button>
        </div>

        {successFiles.length > 0 && (
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs font-medium text-zinc-400">Select all content</span>
            <input
              type="checkbox"
              checked={allSelected}
              onChange={onSelectAll}
              className="h-4 w-4 rounded border-zinc-700 bg-transparent checked:bg-zinc-600 focus:ring-0 focus:ring-offset-0 text-zinc-600 accent-zinc-500 cursor-pointer"
            />
          </div>
        )}

        <div className="space-y-1 mt-2">
          {files.map((file) => {
            // 1. Pending/Processing states (Skeleton loader with dismiss button)
            if (file.status === "pending" || file.status === "processing") {
              return (
                <div
                  key={file.id}
                  className="relative flex items-center justify-between p-2 rounded-lg bg-zinc-800/10 border border-zinc-800/30 group"
                  title={`Uploading and processing: ${file.name}`}
                >
                  <div className="flex items-center gap-3 overflow-hidden w-full min-w-0 pr-6">
                    {/* Placeholder icon */}
                    <div className="w-4 h-4 bg-zinc-700/60 rounded shrink-0 animate-pulse" />
                    <div className="flex flex-col gap-1 w-full min-w-0 animate-pulse">
                      <span className="text-xs text-zinc-500 truncate font-medium">
                        Uploading {file.name}...
                      </span>
                      {/* Premium subtle loader bar */}
                      <div className="h-1 bg-zinc-800 rounded-full w-5/6 overflow-hidden">
                        <div className="h-full bg-blue-500/60 rounded-full animate-pulse" style={{ width: '40%' }} />
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDismissFile(file.id);
                    }}
                    className="absolute right-2 top-2.5 text-zinc-500 hover:text-red-400 p-0.5 rounded transition-colors cursor-pointer z-10 shrink-0"
                    title="Cancel upload"
                  >
                    <X size={14} />
                  </button>
                </div>
              );
            }

            // 2. Failed state (Red card with error message & dismiss x button)
            if (file.status === "failed") {
              return (
                <div
                  key={file.id}
                  className="relative flex flex-col gap-1 p-2 rounded-lg border border-red-500/20 bg-red-950/5 select-none group"
                  title={`Upload failed: ${file.error || "Unknown error"}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-3 overflow-hidden flex-grow min-w-0">
                      <AlertCircle size={16} className="text-red-500 shrink-0" />
                      <span className="text-sm font-medium text-red-300 truncate" title={file.name}>
                        {file.name}
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDismissFile(file.id);
                      }}
                      className="text-zinc-500 hover:text-red-400 p-0.5 rounded transition-colors cursor-pointer shrink-0"
                      title="Dismiss"
                    >
                      <X size={14} />
                    </button>
                  </div>
                  {file.error && (
                    <span className="text-[10px] text-red-400 font-medium pl-7 truncate">
                      {file.error}
                    </span>
                  )}
                </div>
              );
            }

            // 3. Success state (Normal file card with Hover Menu & Inline Rename)
            const isViewing = viewingFileId === file.id;
            const isEditing = editingFileId === file.id;

            return (
              <div
                key={file.id}
                className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors group ${
                  isViewing ? "bg-zinc-800/50" : "hover:bg-zinc-800/30"
                }`}
                onClick={() => {
                  if (!isEditing) onFileClick(file.id);
                }}
              >
                <div className="flex items-center gap-3 overflow-hidden flex-grow min-w-0">
                  <FileText size={16} className="text-red-400 shrink-0" />
                  {isEditing ? (
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          if (editName.trim()) {
                            onRenameFile(file.id, editName.trim());
                          }
                          setEditingFileId(null);
                        } else if (e.key === "Escape") {
                          setEditingFileId(null);
                        }
                      }}
                      onBlur={() => {
                        if (editName.trim()) {
                          onRenameFile(file.id, editName.trim());
                        }
                        setEditingFileId(null);
                      }}
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                      className="bg-zinc-900 text-sm text-white border border-zinc-700 rounded px-1 py-0.5 w-full focus:outline-none focus:border-zinc-500"
                    />
                  ) : (
                    <span className="text-sm text-zinc-300 truncate" title={file.name}>
                      {file.name}
                    </span>
                  )}
                </div>

                {!isEditing && (
                  <div className="flex items-center gap-1 shrink-0 animate-fade-in" onClick={(e) => e.stopPropagation()}>
                    {/* Three-dot dropdown menu trigger */}
                    <div className="relative flex items-center">
                      <button
                        onClick={() =>
                          setActiveMenuFileId(activeMenuFileId === file.id ? null : file.id)
                        }
                        className="opacity-0 group-hover:opacity-100 focus:opacity-100 p-1 hover:bg-zinc-700/60 rounded text-zinc-400 hover:text-white shrink-0 transition-opacity cursor-pointer flex items-center justify-center"
                        title="Document options"
                      >
                        <MoreHorizontal size={14} />
                      </button>

                      {activeMenuFileId === file.id && (
                        <>
                          <div
                            className="fixed inset-0 z-45"
                            onClick={() => setActiveMenuFileId(null)}
                          />
                          <div className="absolute right-0 mt-6 w-28 bg-[#18181b] border border-zinc-800 rounded-lg shadow-xl py-1 z-50 animate-in fade-in slide-in-from-top-1 duration-100">
                            <button
                              onClick={() => {
                                setActiveMenuFileId(null);
                                setEditingFileId(file.id);
                                setEditName(file.name);
                              }}
                              className="w-full text-left px-3 py-1.5 text-xs text-zinc-300 hover:text-white hover:bg-zinc-800/80 transition-colors flex items-center gap-2"
                            >
                              Rename
                            </button>
                            <button
                              onClick={() => {
                                if (confirm(`Are you sure you want to delete "${file.name}"?`)) {
                                  onDeleteFile(file.id);
                                }
                                setActiveMenuFileId(null);
                              }}
                              className="w-full text-left px-3 py-1.5 text-xs text-red-400 hover:text-red-300 hover:bg-red-950/20 transition-colors flex items-center gap-2"
                            >
                              Delete
                            </button>
                          </div>
                        </>
                      )}
                    </div>

                    <input
                      type="checkbox"
                      checked={selectedFileIds.has(file.id)}
                      onChange={() => onSelectFile(file.id)}
                      className="h-4 w-4 rounded border-zinc-700 bg-transparent checked:bg-zinc-600 focus:ring-0 focus:ring-offset-0 text-zinc-600 accent-zinc-500 cursor-pointer ml-1 shrink-0"
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
};

export default ContentPanel;
