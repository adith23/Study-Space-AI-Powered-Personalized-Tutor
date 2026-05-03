"use client";

import { useEffect, useRef, useState } from "react";
import { useDocClient } from "@/hooks/useDocClient";
import { Loader2, X, AlertTriangle } from "lucide-react";
import "@/styles/udoc-overrides.css";

interface DocumentViewerProps {
  fileId: number;
  fileName: string;
  onClose: () => void;
}

export default function DocumentViewer({
  fileId,
  fileName,
  onClose,
}: DocumentViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const { client, isReady, error: clientError } = useDocClient();
  const [isLoading, setIsLoading] = useState(true);
  const [viewerError, setViewerError] = useState<string | null>(null);

  useEffect(() => {
    if (!isReady || !client || !containerRef.current) return;

    let destroyed = false;

    (async () => {
      try {
        const viewer = await client.createViewer({
          container: containerRef.current!,
          theme: "dark",
          zoomMode: "fit-spread-width",
          hideAttribution: false,
        });

        if (destroyed) {
          viewer.destroy();
          return;
        }

        viewer.on("document:load", () => {
          if (!destroyed) setIsLoading(false);
        });

        viewer.on("error", ({ error }: { error: unknown }) => {
          if (!destroyed) {
            setViewerError(
              error instanceof Error ? error.message : "Failed to render document",
            );
            setIsLoading(false);
          }
        });

        viewerRef.current = viewer;
        await viewer.load(`/api/files/${fileId}/content`);
      } catch (err) {
        if (!destroyed) {
          setViewerError(
            err instanceof Error ? err.message : "Failed to load document",
          );
          setIsLoading(false);
        }
      }
    })();

    return () => {
      destroyed = true;
      viewerRef.current?.destroy();
      viewerRef.current = null;
    };
  }, [client, isReady, fileId]);

  const hasError = clientError || viewerError;

  return (
    <div className="flex flex-col h-full bg-[#1e1f22]">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-zinc-800 bg-[#1e1f22] flex-shrink-0">
        <h2 className="text-sm font-semibold text-white">Document Viewer</h2>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-zinc-400 truncate max-w-xs" title={fileName}>
            {fileName}
          </span>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white transition-colors"
            title="Close viewer"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Viewer area */}
      <div className="flex-grow relative min-h-0">
        {/* Loading overlay */}
        {isLoading && !hasError && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#1e1f22]">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
              <p className="text-sm text-zinc-400">Loading document…</p>
            </div>
          </div>
        )}

        {/* Error state */}
        {hasError && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#1e1f22]">
            <div className="flex flex-col items-center gap-3 text-center px-6">
              <AlertTriangle className="h-8 w-8 text-red-400" />
              <p className="text-sm text-red-300">
                {clientError || viewerError}
              </p>
            </div>
          </div>
        )}

        {/* udoc-viewer container */}
        <div
          ref={containerRef}
          className="w-full h-full"
        />
      </div>
    </div>
  );
}
