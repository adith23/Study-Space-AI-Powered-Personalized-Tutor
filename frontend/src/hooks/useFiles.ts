import { useState, useEffect } from "react";
import { listFiles, getFileStatus, uploadFile } from "@/lib/api/files";
import type { UploadedFileState, UploadedFileListResponse, UploadedFileUploadResponse } from "@/types/dashboard";

const VALID_FILE_STATUSES = new Set<UploadedFileState["status"]>([
  "pending",
  "processing",
  "success",
  "failed",
]);

function normalizeFileStatus(status: string | undefined): UploadedFileState["status"] {
  if (status && VALID_FILE_STATUSES.has(status as UploadedFileState["status"])) {
    return status as UploadedFileState["status"];
  }
  return "pending";
}

function normalizeUploadedFile(
  file: UploadedFileListResponse | UploadedFileUploadResponse
): UploadedFileState {
  return {
    id: file.id,
    name: file.name ?? "Untitled document",
    status: normalizeFileStatus(file.status),
  };
}

export function useFiles(setMiddleColumnView: (view: "document" | "quiz" | "flashcard") => void) {
  const [files, setFiles] = useState<UploadedFileState[]>([]);
  const [viewingFileId, setViewingFileId] = useState<number | null>(null);
  const [selectedFileIds, setSelectedFileIds] = useState<Set<number>>(new Set());

  // Initial Fetch
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const filesRes = await listFiles();
        setFiles(filesRes.map(normalizeUploadedFile));
      } catch (error) {
        console.error("Failed to fetch initial files:", error);
      }
    };
    fetchFiles();
  }, []);

  // Poll File Status
  useEffect(() => {
    const activePolls = new Map<number, ReturnType<typeof setInterval>>();

    const pollStatus = async (fileId: number) => {
      try {
        const response = await getFileStatus(fileId);
        const newStatus = response.status;
        setFiles((prevFiles) =>
          prevFiles.map((f) => (f.id === fileId ? { ...f, status: newStatus } : f))
        );
        if (newStatus === "success" || newStatus === "failed") {
          clearInterval(activePolls.get(fileId));
          activePolls.delete(fileId);
        }
      } catch (error) {
        console.error(`Failed to poll status for file ${fileId}:`, error);
        clearInterval(activePolls.get(fileId));
        activePolls.delete(fileId);
      }
    };

    files.forEach((file) => {
      if ((file.status === "pending" || file.status === "processing") && !activePolls.has(file.id)) {
        const intervalId = setInterval(() => pollStatus(file.id), 3000);
        activePolls.set(file.id, intervalId);
      }
    });

    return () => {
      activePolls.forEach((intervalId) => clearInterval(intervalId));
    };
  }, [files]);

  const handleFileUpload = async (file: File) => {
    const formData = new FormData();
    formData.append("file_type", "pdf");
    formData.append("file", file);
    formData.append("name", file.name);

    try {
      const response = await uploadFile(file);
      const uploaded = normalizeUploadedFile(response);
      setFiles((prev) => {
        const deduped = prev.filter((fileItem) => fileItem.id !== uploaded.id);
        return [uploaded, ...deduped];
      });
      setViewingFileId(uploaded.id);
      setMiddleColumnView("document");
    } catch (error) {
      console.error("Upload failed", error);
    }
  };

  const handleFileClick = (fileId: number) => {
    setViewingFileId(fileId);
    setMiddleColumnView("document");
  };

  const handleSelectAllFiles = () => {
    if (selectedFileIds.size === files.length) {
      setSelectedFileIds(new Set());
    } else {
      setSelectedFileIds(new Set(files.map((f) => f.id)));
    }
  };

  const handleSelectFile = (id: number) => {
    setSelectedFileIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const viewingFile = viewingFileId
    ? files.find((f) => f.id === viewingFileId) ?? null
    : null;

  return {
    files,
    viewingFileId,
    setViewingFileId,
    viewingFile,
    selectedFileIds,
    setSelectedFileIds,
    handleFileUpload,
    handleFileClick,
    handleSelectAllFiles,
    handleSelectFile
  };
}
