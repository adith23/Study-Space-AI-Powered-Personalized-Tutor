import React from "react";
import { ChevronsLeft, Plus, Search, FileText } from "lucide-react";
import type { UploadedFileState } from "@/types/dashboard";

interface ContentPanelProps {
  files: UploadedFileState[];
  selectedFileIds: Set<number>;
  onSelectFile: (id: number) => void;
  onSelectAll: () => void;
  onAddContent: () => void;
  onFileClick: (id: number) => void;
  viewingFileId: number | null;
}

const ContentPanel: React.FC<ContentPanelProps> = ({
  files,
  selectedFileIds,
  onSelectFile,
  onSelectAll,
  onAddContent,
  onFileClick,
  viewingFileId
}) => {
  const allSelected = files.length > 0 && selectedFileIds.size === files.length;

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
            className="flex-1 flex items-center justify-center gap-2 py-1.5 rounded-full border border-zinc-700 bg-transparent text-sm text-zinc-300 hover:text-white hover:bg-zinc-800 transition-colors"
          >
            <Plus size={16} />
            Add Content
          </button>
          <button className="flex-1 flex items-center justify-center gap-2 py-1.5 rounded-full border border-zinc-700 bg-transparent text-sm text-zinc-300 hover:text-white hover:bg-zinc-800 transition-colors">
            <Search size={16} />
            Search
          </button>
        </div>

        {files.length > 0 && (
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
          {files.map((file) => (
            <div
              key={file.id}
              className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                viewingFileId === file.id ? "bg-zinc-800/50" : "hover:bg-zinc-800/30"
              }`}
              onClick={() => onFileClick(file.id)}
            >
              <div className="flex items-center gap-3 overflow-hidden">
                <FileText size={16} className="text-red-400 shrink-0" />
                <span className="text-sm text-zinc-300 truncate" title={file.name}>
                  {file.name}
                </span>
              </div>
              <div onClick={(e) => e.stopPropagation()}>
                <input
                  type="checkbox"
                  checked={selectedFileIds.has(file.id)}
                  onChange={() => onSelectFile(file.id)}
                  className="h-4 w-4 rounded border-zinc-700 bg-transparent checked:bg-zinc-600 focus:ring-0 focus:ring-offset-0 text-zinc-600 accent-zinc-500 cursor-pointer ml-2 shrink-0"
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};

export default ContentPanel;
