import { useEffect, type Dispatch, type SetStateAction } from "react";
import { useSpaceStore } from "@/stores/spaceStore";
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

function normalizeFileStatus(
  status: string | undefined,
): UploadedFileState["status"] {
  if (
    status &&
    VALID_FILE_STATUSES.has(status as UploadedFileState["status"])
  ) {
    return status as UploadedFileState["status"];
  }
  return "pending";
}

export function normalizeUploadedFile(
  file: UploadedFileListResponse | UploadedFileUploadResponse,
): UploadedFileState {
  return {
    id: file.id,
    name: file.name ?? "Untitled document",
    status: normalizeFileStatus(file.status),
    error: file.error_message,
  };
}

export function useFiles(
  spaceId: number,
  initialFiles: UploadedFileListResponse[],
  setMiddleColumnView: (view: "document" | "quiz" | "flashcard") => void,
) {
  const {
    files,
    viewingFileId,
    selectedFileIds,
    setFiles,
    addFile,
    updateFile,
    removeFile,
    setViewingFileId,
    toggleFileSelection,
    setSelectedFileIds: setStoreSelectedFileIds,
    clearSelections,
  } = useSpaceStore();

  const setSelectedFileIds: Dispatch<SetStateAction<Set<number>>> = (value) => {
    if (typeof value === "function") {
      const current = useSpaceStore.getState().selectedFileIds;
      setStoreSelectedFileIds(value(current));
    } else {
      setStoreSelectedFileIds(value);
    }
  };

  // Populate files list when initialFiles changes
  useEffect(() => {
    setFiles(initialFiles.map(normalizeUploadedFile));
  }, [initialFiles, setFiles]);

  // Connect to SSE status stream for real-time updates (replaces polling)
  useEffect(() => {
    const eventSource = new EventSource(
      "/api/v1/materials/files/status/stream",
    );

    eventSource.onmessage = (event) => {
      try {
        const updatedFiles = JSON.parse(event.data);
        if (Array.isArray(updatedFiles)) {
          updatedFiles.forEach((file: any) => {
            updateFile(file.id, {
              status: normalizeFileStatus(file.status),
              error: file.error_message || undefined,
            });
          });
        }
      } catch (err) {
        console.error("Failed to parse SSE message:", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE connection error:", err);
    };

    return () => {
      eventSource.close();
    };
  }, [updateFile]);

  const handleFileUpload = async (file: File) => {
    const tempId = -Math.floor(Math.random() * 1000000000) - 1;
    const tempFile: UploadedFileState = {
      id: tempId,
      name: file.name,
      status: "pending",
    };

    // Add temp file to files list immediately to trigger skeleton loader
    addFile(tempFile);

    const formData = new FormData();
    formData.append("file_type", "pdf");
    formData.append("file", file);
    formData.append("name", file.name);

    try {
      const result = await uploadFileAction(spaceId, formData);

      if (result.error || !result.data) {
        updateFile(tempId, {
          status: "failed",
          error: result.error || "Upload failed",
        });
        return;
      }

      const uploaded = normalizeUploadedFile(result.data);

      let wasDismissed = false;

      // Check if temporary file is still in the files array before replacing it
      const currentFiles = useSpaceStore.getState().files;
      const exists = currentFiles.some((f) => f.id === tempId);

      if (!exists) {
        wasDismissed = true;
        // Clean up the uploaded file on the backend since it was dismissed in the UI
        deleteFileAction(uploaded.id).catch((err) =>
          console.error("Failed to delete orphaned upload:", err),
        );
        return;
      }

      // Replace temp ID with actual uploaded file details
      removeFile(tempId);
      addFile(uploaded);

      if (!wasDismissed) {
        setViewingFileId(uploaded.id);
        setMiddleColumnView("document");
      }
    } catch (error: any) {
      console.error("Upload failed", error);
      const errorMessage = error?.message || "Upload failed";
      updateFile(tempId, {
        status: "failed",
        error: errorMessage,
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
      clearSelections();
    } else {
      setSelectedFileIds(new Set(successFiles.map((f) => f.id)));
    }
  };

  const handleSelectFile = (id: number) => {
    toggleFileSelection(id);
  };

  const handleRenameFile = async (fileId: number, newName: string) => {
    try {
      const res = await renameFileAction(fileId, newName);
      if (!res.error) {
        updateFile(fileId, { name: newName });
      }
    } catch (error) {
      console.error("Failed to rename file", error);
    }
  };

  const handleDeleteFile = async (fileId: number) => {
    try {
      const res = await deleteFileAction(fileId);
      if (!res.error) {
        removeFile(fileId);
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
      removeFile(fileId);
    }
  };

  const viewingFile = viewingFileId
    ? (files.find((f) => f.id === viewingFileId) ?? null)
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
    handleDismissFile,
  };
}
