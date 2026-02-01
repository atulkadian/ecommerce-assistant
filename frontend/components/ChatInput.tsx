"use client";

import { useState, KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");

  const send = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input.trim());
      setInput("");
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="flex gap-2">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Ask about products..."
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none rounded-2xl border border-border/50 bg-background/50 px-4 py-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 min-h-[52px] max-h-[200px]"
      />
      <button
        onClick={send}
        disabled={disabled || !input.trim()}
        className="flex items-center justify-center rounded-2xl px-4 py-3 bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
      >
        <Send className="h-5 w-5" />
      </button>
    </div>
  );
}
