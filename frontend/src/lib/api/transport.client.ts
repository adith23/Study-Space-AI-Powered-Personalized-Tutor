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
 * Fetch helper with AbortController timeout and exponential backoff retry.
 */
async function fetchWithTimeoutAndRetry(
  url: string,
  init: RequestInit,
  retries = 3,
  timeoutMs = 15000,
): Promise<Response> {
  let attempt = 0;
  while (true) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const res = await fetch(url, {
        ...init,
        signal: controller.signal,
      });
      clearTimeout(id);

      // Only retry on transient server-side errors (5xx)
      if (res.status >= 500 && attempt < retries) {
        attempt++;
        const backoffDelay = Math.pow(2, attempt) * 1000 + Math.random() * 200;
        await new Promise((resolve) => setTimeout(resolve, backoffDelay));
        continue;
      }

      return res;
    } catch (err: any) {
      clearTimeout(id);
      const isAbort = err.name === "AbortError";
      // Fetch throws a TypeError for network connectivity/CORS errors
      const isNetwork = err instanceof TypeError;

      if ((isAbort || isNetwork) && attempt < retries) {
        attempt++;
        const backoffDelay = Math.pow(2, attempt) * 1000 + Math.random() * 200;
        await new Promise((resolve) => setTimeout(resolve, backoffDelay));
        continue;
      }
      throw err;
    }
  }
}

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

  const timeout = options.timeout ?? 30000;
  const retries = options.retries ?? 2;

  const res = await fetchWithTimeoutAndRetry(
    `/api/v1${path}`,
    {
      method: options.method || "GET",
      headers,
      body: options.body,
    },
    retries,
    timeout,
  );

  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      const loginUrl = new URL("/login", window.location.origin);
      loginUrl.searchParams.set("expired", "1");
      window.location.assign(loginUrl.toString());
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
