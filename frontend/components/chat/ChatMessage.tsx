import { memo } from "react";
import { User, Bot } from "lucide-react";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export const ChatMessage = memo(function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 py-4 ${isUser ? "justify-end" : ""}`}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--primary)] text-[var(--primary-foreground)]">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 text-sm leading-relaxed ${
          isUser
            ? "bg-[var(--primary)] text-[var(--primary-foreground)]"
            : "bg-[var(--muted)]"
        }`}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>
      </div>
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--muted)]">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
});
