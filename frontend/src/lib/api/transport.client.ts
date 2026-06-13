/**
 * Client-side transport for the centralized API contract.
 *
 * Runs in the BROWSER only. Used by:
 *   - Client hooks for polling (useVideoGeneration, useFiles)
 *   - Client components for on-demand fetching (QuizViewer, FlashcardViewer, ChatInterface)
 *
 * Requests go through the Next.js rewrite proxy (/api/v1/* → FastAPI).
 * The browser automatically sends the HttpOnly cookie.
 */

import type { FetcherOptions } from "./types";

/**
 * Client-side fetcher using native browser fetch.
 * Satisfies the Fetcher interface — can be passed to any endpoint factory.
 */
export async function clientTransport<T>(
  path: string,
  options: FetcherOptions = {},
): Promise<T> {
  const headers: Record<string, string> = { ...options.headers };

  // Only set Content-Type for non-FormData bodies
  const isFormData =
    typeof options.body === "object" &&
    options.body !== null &&
    options.body instanceof FormData;
  if (!headers["Content-Type"] && !isFormData) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`/api/v1${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body,
  });

  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      window.location.href = "/login";
    }
    const body = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${body}`);
  }

  // Handle 204 No Content
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
