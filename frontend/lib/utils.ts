/**
 * Shared utility functions.
 */

/**
 * Fetch with a timeout. Aborts the request if it exceeds `ms` milliseconds.
 */
export function fetchWithTimeout(
  url: string,
  init?: RequestInit,
  ms = 30_000,
): Promise<Response> {
  const controller = new AbortController();
  const existing = init?.signal;

  // If caller provided their own signal, forward its abort
  if (existing) {
    if (existing.aborted) {
      controller.abort(existing.reason);
    } else {
      existing.addEventListener("abort", () => controller.abort(existing.reason), { once: true });
    }
  }

  const timeout = setTimeout(() => controller.abort(new Error("Request timed out")), ms);
  return fetch(url, { ...init, signal: controller.signal }).finally(() => clearTimeout(timeout));
}

/**
 * Retry a fetch up to `maxRetries` times with exponential backoff.
 * Only retries on network errors and 5xx status codes.
 */
export async function fetchWithRetry(
  url: string,
  init?: RequestInit,
  maxRetries = 2,
  timeoutMs = 30_000,
): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetchWithTimeout(url, init, timeoutMs);
      // Only retry on server errors (5xx), not client errors (4xx)
      if (res.status >= 500 && attempt < maxRetries) {
        await new Promise((r) => setTimeout(r, 1000 * 2 ** attempt));
        continue;
      }
      return res;
    } catch (err) {
      lastError = err;
      // Don't retry AbortErrors (intentional abort)
      if (err instanceof DOMException && err.name === "AbortError") throw err;
      if (attempt < maxRetries) {
        await new Promise((r) => setTimeout(r, 1000 * 2 ** attempt));
      }
    }
  }
  throw lastError;
}
