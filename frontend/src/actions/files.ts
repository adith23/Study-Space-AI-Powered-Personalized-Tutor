"use server";

import { api } from "@/lib/api/index.server";
import { isNextRedirectError } from "@/lib/api/transport.server";


export async function uploadFileAction(spaceId: number, formData: FormData) {
  try {
    const data = await api.spaces.uploadFile(spaceId, formData);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Upload failed",
      data: null,
    };
  }
}

export async function getFileStatusAction(fileId: number) {
  return api.files.getStatus(fileId);
}

export async function renameFileAction(fileId: number, newName: string) {
  try {
    await api.files.rename(fileId, newName);
    return { error: null };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return { error: err instanceof Error ? err.message : "Rename failed" };
  }
}

export async function deleteFileAction(fileId: number) {
  try {
    await api.files.delete(fileId);
    return { error: null };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return { error: err instanceof Error ? err.message : "Delete failed" };
  }
}

