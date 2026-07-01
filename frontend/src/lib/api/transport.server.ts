/**
 * Server-side transport for the centralized API contract.
 *
 * Runs on Next.js server ONLY. Used by:
 *   - Server Components (page.tsx, layout.tsx)
 *   - Server Actions ("use server" functions)
 *   - Route Handlers (route.ts)
 *
 * Reads JWT from HttpOnly cookies and attaches it as a Bearer header.
 * Calls the backend via INTERNAL_BACKEND_URL (private, never exposed to client).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { FetcherOptions } from "./types";

const BACKEND_URL =
  process.env.INTERNAL_BACKEND_URL || "http://127.0.0.1:8000/api/v1";
const LOGIN_EXPIRED_URL = "/login?expired=1";

export function isNextRedirectError(error: unknown) {
  return (
    typeof error === "object" &&
    error !== null &&
    "digest" in error &&
    typeof error.digest === "string" &&
    error.digest.startsWith("NEXT_REDIRECT")
  );
}

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
        console.warn(`[API Server Transport] Transient 5xx response (${res.status}) on attempt ${attempt + 1} for URL: ${url}. Retrying...`);
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

      console.error(`[API Server Transport] Fetch failed on attempt ${attempt + 1} to URL: ${url}. Error:`, err.message || err);

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
 * Authenticated server-side fetcher.
 * Satisfies the Fetcher interface — can be passed to any endpoint factory.
 */
export async function serverTransport<T>(
  path: string,
  options: FetcherOptions = {},
): Promise<T> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;

  if (!token) {
    redirect(LOGIN_EXPIRED_URL);
  }

  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);

  // Only set Content-Type for non-FormData bodies
  const isFormData =
    typeof options.body === "object" &&
    options.body !== null &&
    options.body instanceof FormData;
  if (!headers.has("Content-Type") && !isFormData) {
    headers.set("Content-Type", "application/json");
  }

  const timeout = options.timeout ?? 30000;
  const retries = options.retries ?? 2;

  const res = await fetchWithTimeoutAndRetry(
    `${BACKEND_URL}${path}`,
    {
      method: options.method || "GET",
      headers,
      body: options.body,
      cache: "no-store" as RequestCache,
    },
    retries,
    timeout,
  );

  if (res.status === 401) {
    redirect(LOGIN_EXPIRED_URL);
  }

  if (!res.ok) {
    const body = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${body}`);
  }

  // Handle 204 No Content (e.g., DELETE responses)
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

/**
 * Raw server fetch that returns the Response object directly.
 * Used by Route Handlers that need to stream the response body
 * (e.g., video streaming, PDF content, thumbnails).
 */
export async function serverTransportRaw(
  path: string,
  options: FetcherOptions = {},
): Promise<Response> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;

  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const timeout = options.timeout ?? 30000;
  const retries = options.retries ?? 2;

  return fetchWithTimeoutAndRetry(
    `${BACKEND_URL}${path}`,
    {
      method: options.method || "GET",
      headers,
      body: options.body,
    },
    retries,
    timeout,
  );
}
