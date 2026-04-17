import { api } from "./client";
import type { UploadedFileState, UploadedFileListResponse, UploadedFileUploadResponse } from "@/types/dashboard";

export async function listFiles() {
  const response = await api.get<UploadedFileListResponse[]>("/materials/files");
  return response.data;
}

export async function getFileStatus(fileId: number) {
  const response = await api.get<{ status: UploadedFileState["status"] }>(`/materials/${fileId}/status`);
  return response.data;
}

export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append("file_type", "pdf");
  formData.append("file", file);
  formData.append("name", file.name);

  const response = await api.post<UploadedFileUploadResponse>("/materials/file", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}
