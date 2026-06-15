import { useState, useEffect } from "react";
import { clientApi } from "@/lib/api/index.client";
import {
  uploadFileAction,
  renameFileAction,
  deleteFileAction,
} from "@/actions/files";
import type {
  UploadedFileState,
  UploadedFileListResponse,
  UploadedFileUploadResponse,
} from "@/types/dashboard";

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

export function normalizeUploadedFile(
  file: UploadedFileListResponse | UploadedFileUploadResponse
): UploadedFileState {
  return {
    id: file.id,
    name: file.name ?? "Untitled document",
    status: normalizeFileStatus(file.status),
    error: file.error_message,
  };
}

export function useFiles(
  initialFiles: UploadedFileListResponse[],
  setMiddleColumnView: (view: "document" | "quiz" | "flashcard") => void,
) {
  const [files, setFiles] = useState<UploadedFileState[]>(
    initialFiles.map(normalizeUploadedFile),
  );
  const [viewingFileId, setViewingFileId] = useState<number | null>(null);
  const [selectedFileIds, setSelectedFileIds] = useState<Set<number>>(new Set());

  // Poll File Status — uses clientApi for client-side polling
  useEffect(() => {
    const activePolls = new Map<number, ReturnType<typeof setInterval>>();

    const pollStatus = async (fileId: number) => {
      try {
        const response = await clientApi.files.getStatus(fileId);
        const newStatus = response.status;
        const errorMsg = response.error_message;
        setFiles((prevFiles) =>
          prevFiles.map((f) =>
            f.id === fileId ? { ...f, status: newStatus, error: errorMsg } : f
          )
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
      // Only poll for valid database IDs (> 0) that are still pending or processing
      if (
        file.id > 0 &&
        (file.status === "pending" || file.status === "processing") &&
        !activePolls.has(file.id)
      ) {
        const intervalId = setInterval(() => pollStatus(file.id), 3000);
        activePolls.set(file.id, intervalId);
      }
    });

    return () => {
      activePolls.forEach((intervalId) => clearInterval(intervalId));
    };
  }, [files]);

  const handleFileUpload = async (file: File) => {
    const tempId = -Math.floor(Math.random() * 1000000000) - 1;
    const tempFile: UploadedFileState = {
      id: tempId,
      name: file.name,
      status: "pending",
    };

    // Add temp file to files list immediately to trigger skeleton loader
    setFiles((prev) => [tempFile, ...prev]);

    const formData = new FormData();
    formData.append("file_type", "pdf");
    formData.append("file", file);
    formData.append("name", file.name);

    try {
      const result = await uploadFileAction(formData);

      if (result.error || !result.data) {
        setFiles((prev) => {
          const exists = prev.some((f) => f.id === tempId);
          if (!exists) return prev;
          return prev.map((f) =>
            f.id === tempId
              ? { ...f, status: "failed", error: result.error || "Upload failed" }
              : f
          );
        });
        return;
      }

      const uploaded = normalizeUploadedFile(result.data);

      let wasDismissed = false;
      setFiles((prev) => {
        const exists = prev.some((f) => f.id === tempId);
        if (!exists) {
          wasDismissed = true;
          // Clean up the uploaded file on the backend since it was dismissed in the UI
          deleteFileAction(uploaded.id).catch((err) =>
            console.error("Failed to delete orphaned upload:", err)
          );
          return prev;
        }
        return prev.map((f) => (f.id === tempId ? uploaded : f));
      });

      if (!wasDismissed) {
        setViewingFileId(uploaded.id);
        setMiddleColumnView("document");
      }
    } catch (error: any) {
      console.error("Upload failed", error);
      const errorMessage = error?.message || "Upload failed";
      setFiles((prev) => {
        const exists = prev.some((f) => f.id === tempId);
        if (!exists) return prev;
        return prev.map((f) =>
          f.id === tempId
            ? { ...f, status: "failed", error: errorMessage }
            : f
        );
      });
    }
  };

  const handleFileClick = (fileId: number) => {
    const file = files.find((f) => f.id === fileId);
    if (!file || file.status !== "success") return;
    setViewingFileId(fileId);
    setMiddleColumnView("document");
  };

  const handleSelectAllFiles = () => {
    const successFiles = files.filter((f) => f.status === "success");
    if (selectedFileIds.size === successFiles.length) {
      setSelectedFileIds(new Set());
    } else {
      setSelectedFileIds(new Set(successFiles.map((f) => f.id)));
    }
  };

  const handleSelectFile = (id: number) => {
    const file = files.find((f) => f.id === id);
    if (!file || file.status !== "success") return;
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

  const handleRenameFile = async (fileId: number, newName: string) => {
    try {
      await renameFileAction(fileId, newName);
      setFiles((prev) =>
        prev.map((f) => (f.id === fileId ? { ...f, name: newName } : f))
      );
    } catch (error) {
      console.error("Failed to rename file", error);
    }
  };

  const handleDeleteFile = async (fileId: number) => {
    try {
      await deleteFileAction(fileId);
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
      setSelectedFileIds((prev) => {
        const next = new Set(prev);
        next.delete(fileId);
        return next;
      });
      if (viewingFileId === fileId) {
        setViewingFileId(null);
      }
    } catch (error) {
      console.error("Failed to delete file", error);
    }
  };

  const handleDismissFile = async (fileId: number) => {
    try {
      if (fileId > 0) {
        await deleteFileAction(fileId);
      }
    } catch (error) {
      console.error("Failed to dismiss failed file:", error);
    } finally {
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
      setSelectedFileIds((prev) => {
        const next = new Set(prev);
        next.delete(fileId);
        return next;
      });
      if (viewingFileId === fileId) {
        setViewingFileId(null);
      }
    }
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
    handleSelectFile,
    handleRenameFile,
    handleDeleteFile,
    handleDismissFile
  };
}
