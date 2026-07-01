"use server";

import { api } from "@/lib/api/index.server";
import { isNextRedirectError } from "@/lib/api/transport.server";
import type { SpaceCreatePayload, SpaceUpdatePayload } from "@/types/space";
import type { ActionResult } from "@/types";

export async function listSpacesAction(): Promise<ActionResult<any>> {
  try {
    const data = await api.spaces.list();
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to list spaces",
      data: null,
    };
  }
}

export async function createSpaceAction(payload: SpaceCreatePayload): Promise<ActionResult<any>> {
  try {
    const data = await api.spaces.create(payload);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to create space",
      data: null,
    };
  }
}

export async function getSpaceAction(spaceId: number): Promise<ActionResult<any>> {
  try {
    const data = await api.spaces.get(spaceId);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Space not found",
      data: null,
    };
  }
}

export async function updateSpaceAction(
  spaceId: number,
  payload: SpaceUpdatePayload,
): Promise<ActionResult<any>> {
  try {
    const data = await api.spaces.update(spaceId, payload);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to update space",
      data: null,
    };
  }
}

export async function deleteSpaceAction(spaceId: number): Promise<ActionResult<void>> {
  try {
    await api.spaces.delete(spaceId);
    return { error: null, data: null };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to delete space",
      data: null,
    };
  }
}

export async function exploreSpacesAction(query?: string): Promise<ActionResult<any>> {
  try {
    const data = await api.spaces.explore(query);
    return { error: null, data };
  } catch (err) {
    if (isNextRedirectError(err)) throw err;
    return {
      error: err instanceof Error ? err.message : "Failed to explore spaces",
      data: null,
    };
  }
}
