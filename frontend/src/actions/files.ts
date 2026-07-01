"use server";

import { api } from "@/lib/api/index.server";
import { isNextRedirectError } from "@/lib/api/transport.server";
import type { ActionResult } from "@/types";

export async function uploadFileAction(
  spaceId: number,
  formData: FormData,
): Promise<ActionResult<any>> {
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

export async function getFileStatusAction(fileId: number): Promise<ActionResult<any>> {
  try {
    const data = await api.files.getStatus(fileId);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to get file status",
      data: null,
    };
  }
}

export async function renameFileAction(
  fileId: number,
  newName: string,
): Promise<ActionResult<void>> {
  try {
    await api.files.rename(fileId, newName);
    return { error: null, data: null };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Rename failed",
      data: null,
    };
  }
}

export async function deleteFileAction(fileId: number): Promise<ActionResult<void>> {
  try {
    await api.files.delete(fileId);
    return { error: null, data: null };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Delete failed",
      data: null,
    };
  }
}
