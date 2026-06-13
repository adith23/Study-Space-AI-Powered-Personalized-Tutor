/**
 * File endpoints — centralized definitions.
 * Every file-related API path is defined here ONCE.
 */

import type { Fetcher } from "../types";
import type {
  UploadedFileListResponse,
  UploadedFileUploadResponse,
  UploadedFileState,
} from "@/types/dashboard";

export function createFilesApi(fetcher: Fetcher) {
  return {
    /** GET /materials/files — List all user's files */
    list: () =>
      fetcher<UploadedFileListResponse[]>("/materials/files"),

    /** POST /materials/file — Upload a file (FormData) */
    upload: (formData: FormData) =>
      fetcher<UploadedFileUploadResponse>("/materials/file", {
        method: "POST",
        body: formData,
        headers: {}, // Let browser/node set Content-Type boundary for FormData
      }),

    /** GET /materials/{fileId}/status — Poll processing status */
    getStatus: (fileId: number) =>
      fetcher<{ status: UploadedFileState["status"]; error_message?: string }>(
        `/materials/${fileId}/status`,
      ),

    /** PUT /materials/files/{fileId}/rename — Rename a file */
    rename: (fileId: number, name: string) =>
      fetcher<UploadedFileUploadResponse>(
        `/materials/files/${fileId}/rename`,
        { method: "PUT", body: JSON.stringify({ name }) },
      ),

    /** DELETE /materials/files/{fileId} — Delete a file */
    delete: (fileId: number) =>
      fetcher<void>(`/materials/files/${fileId}`, { method: "DELETE" }),
  };
}
