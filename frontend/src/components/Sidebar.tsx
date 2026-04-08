import React from "react";
import {
  MessageSquarePlus,
  MessageSquare,
  Loader2,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import type {
  ChatSession,
  UploadedFileState,
} from "./StudySpaceChat"; 

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;
  files: UploadedFileState[];
}

const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  files,
}) => {
  return (
    <aside className="w-1/3 bg-zinc-900 p-4 flex flex-col space-y-6 overflow-y-auto border-r border-zinc-700">
      <div>
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-xl font-bold">Chats</h2>
          <button
            onClick={onCreateSession}
            className="p-1 hover:bg-zinc-700 rounded"
            title="Create new chat"
          >
            <MessageSquarePlus size={20} />
          </button>
        </div>
        <div className="space-y-2">
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => onSelectSession(session.id)}
              className={`w-full text-left px-3 py-2 rounded-md flex items-center gap-2 transition-colors ${
                activeSessionId === session.id
                  ? "bg-blue-600"
                  : "hover:bg-zinc-700"
              }`}
            >
              <MessageSquare size={16} /> {session.name}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-grow">
        <h2 className="text-xl font-bold mb-2">Documents</h2>
        <div className="space-y-1 mt-4">
          {files.length === 0 && (
            <p className="text-sm text-zinc-500">No documents uploaded yet.</p>
          )}
          {files.map((file) => (
            <div
              key={file.id}
              className="text-sm text-zinc-400 flex items-center gap-2 p-1"
            >
              {file.status === "success" && (
                <CheckCircle2
                  size={14}
                  className="text-green-500 flex-shrink-0"
                />
              )}
              {file.status === "processing" && (
                <Loader2
                  size={14}
                  className="animate-spin text-blue-500 flex-shrink-0"
                />
              )}
              {file.status === "failed" && (
                <AlertTriangle
                  size={14}
                  className="text-red-500 flex-shrink-0"
                />
              )}
              <span className="truncate" title={file.name}>
                {file.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
