/**
 * Shared hook for consuming Server-Sent Event (SSE) streams from the backend.
 *
 * Eliminates duplicated SSE-parsing logic across ChatInterface,
 * CountryProfile, CountryTransparency, and RAGing pages.
 */

import { useCallback, useRef, useState } from "react";

export interface SSEEvent {
  type: "status" | "token" | "source" | "error" | "done" | "progress" | "complete";
  data?: unknown;
  [key: string]: unknown;
}

export interface UseSSEStreamOptions {
  /** Called for each parsed SSE event */
  onEvent: (event: SSEEvent) => void;
  /** Called when the stream finishes (reader done) */
  onDone?: () => void;
}

export interface UseSSEStreamReturn {
  /** Start streaming from an endpoint */
  startStream: (url: string, body: unknown) => Promise<void>;
  /** Whether a stream is currently active */
  isStreaming: boolean;
  /** Last error message (network / HTTP-level, not SSE error events) */
  error: string | null;
}

const STATUS_MESSAGES: Record<number, string> = {
  429: "The service is receiving too many requests. Please wait a moment and try again.",
  503: "The AI service is temporarily unavailable. Please try again in a few minutes.",
  504: "The request timed out. Please try a simpler question or try again later.",
};

export function useSSEStream({ onEvent, onDone }: UseSSEStreamOptions): UseSSEStreamReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Keep a stable reference to the latest callbacks
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  const startStream = useCallback(async (url: string, body: unknown) => {
    setIsStreaming(true);
    setError(null);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const msg =
          STATUS_MESSAGES[response.status] ||
          `Request failed (${response.status}).`;
        setError(msg);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        setError("No response body received.");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;

          try {
            const event: SSEEvent = JSON.parse(line.slice(6));
            onEventRef.current(event);
          } catch (e) {
            console.warn("[useSSEStream] Failed to parse SSE event:", line, e);
          }
        }
      }

      onDoneRef.current?.();
    } catch {
      setError("Connection lost. Please try again.");
    } finally {
      setIsStreaming(false);
    }
  }, []);

  return { startStream, isStreaming, error };
}
