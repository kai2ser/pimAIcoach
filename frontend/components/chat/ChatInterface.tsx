"use client";

import { useState, useRef, useEffect, useCallback, type FormEvent } from "react";
import { Send, Loader2 } from "lucide-react";
import { ChatMessage, type Message } from "./ChatMessage";
import { SourceCards, type Source } from "./SourceCards";
import { MetadataFilters, type Filters } from "@/components/filters/MetadataFilters";

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [filters, setFilters] = useState<Filters>({});
  const [showFilters, setShowFilters] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamedAnswer = useRef("");

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const updateAssistantMessage = useCallback((text: string) => {
    setMessages((prev) => {
      const updated = [...prev];
      const last = updated[updated.length - 1];
      if (last && last.role === "assistant") {
        updated[updated.length - 1] = { ...last, content: text };
      }
      return updated;
    });
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setSources([]);
    streamedAnswer.current = "";

    try {
      const chatHistory = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const activeFilters = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== undefined && v !== "")
      );

      const response = await fetch("/api/coach/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: input,
          chat_history: chatHistory,
          filters: Object.keys(activeFilters).length > 0 ? activeFilters : null,
          stream: true,
        }),
      });

      if (!response.ok) {
        const statusMessages: Record<number, string> = {
          429: "The service is receiving too many requests. Please wait a moment and try again.",
          503: "The AI service is temporarily unavailable. Please try again in a few minutes.",
          504: "The request timed out. Please try a simpler question or try again later.",
        };
        throw new Error(
          statusMessages[response.status] ||
            "Something went wrong. Please try again."
        );
      }

      // Add empty assistant message that we'll fill with streamed tokens
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE events (separated by double newlines)
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data: ")) continue;

          try {
            const event = JSON.parse(line.slice(6));

            if (event.type === "source") {
              setSources((prev) => [...prev, event.data]);
            } else if (event.type === "token") {
              streamedAnswer.current += event.data;
              updateAssistantMessage(streamedAnswer.current);
            } else if (event.type === "error") {
              // Server sent an error during streaming
              const errorNote =
                "\n\n---\n⚠️ " +
                (event.data ||
                  "An error occurred while generating the answer. Please try again.");
              if (streamedAnswer.current) {
                // Append error note to partial answer
                streamedAnswer.current += errorNote;
                updateAssistantMessage(streamedAnswer.current);
              } else {
                updateAssistantMessage(
                  event.data ||
                    "An error occurred while generating the answer. Please try again."
                );
              }
            }
            // "done" event — loop will end naturally when reader is done
          } catch {
            // Skip malformed JSON lines
          }
        }
      }
    } catch (error) {
      const errorText =
        error instanceof Error && error.message
          ? error.message
          : "Sorry, I encountered an error processing your question. Please try again.";
      const errorMessage: Message = {
        role: "assistant",
        content: errorText,
      };
      // If we already added an empty assistant message, replace it
      if (streamedAnswer.current === "") {
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === "assistant" && last.content === "") {
            return [...prev.slice(0, -1), errorMessage];
          }
          return [...prev, errorMessage];
        });
      } else {
        setMessages((prev) => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-57px)] flex-col">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl">
          {messages.length === 0 && (
            <div className="py-20 text-center text-[var(--muted-foreground)]">
              <p className="mb-2 text-lg font-medium">Welcome to PIM AI Coach</p>
              <p className="text-sm">
                Ask a question about public investment management policies,
                regulations, or best practices.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {[
                  "What are best practices for project appraisal?",
                  "Compare PIM frameworks in Colombia and Kenya",
                  "What legislation governs public investment in Lithuania?",
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => setInput(q)}
                    className="rounded-full border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-[var(--muted)]"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}

          {isLoading && streamedAnswer.current === "" && (
            <div className="flex items-center gap-2 py-4 text-sm text-[var(--muted-foreground)]">
              <Loader2 className="h-4 w-4 animate-spin" />
              Searching policies and generating answer...
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="border-t border-[var(--border)] bg-[var(--muted)] px-4 py-3">
          <div className="mx-auto max-w-3xl">
            <SourceCards sources={sources} />
          </div>
        </div>
      )}

      {/* Filters (collapsible) */}
      {showFilters && (
        <div className="border-t border-[var(--border)] px-4 py-3">
          <div className="mx-auto max-w-3xl">
            <MetadataFilters filters={filters} onChange={setFilters} />
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-[var(--border)] px-4 py-3">
        <form
          onSubmit={handleSubmit}
          className="mx-auto flex max-w-3xl items-center gap-2"
        >
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="rounded-lg border border-[var(--border)] px-3 py-2 text-xs text-[var(--muted-foreground)] hover:bg-[var(--muted)]"
          >
            Filters {Object.values(filters).filter(Boolean).length > 0 && `(${Object.values(filters).filter(Boolean).length})`}
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about PIM policies, regulations, or best practices..."
            className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--background)] px-4 py-2 text-sm outline-none focus:border-[var(--primary)]"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="rounded-lg bg-[var(--primary)] p-2 text-[var(--primary-foreground)] hover:opacity-90 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
