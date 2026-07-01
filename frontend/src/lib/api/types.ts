/**
 * Shared types for the centralized API contract.
 * Both server and client transports satisfy the Fetcher interface.
 */

export interface FetcherOptions {
  method?: string;
  body?: BodyInit | null;
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
}

export type Fetcher = <T>(
  path: string,
  options?: FetcherOptions,
) => Promise<T>;
