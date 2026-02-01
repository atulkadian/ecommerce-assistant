"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message } from "@/types/chat";
import { User, Bot } from "lucide-react";

export function ChatMessage({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="flex max-w-[80%] gap-3">
          <div className="rounded-2xl rounded-tr-md bg-primary px-4 py-3">
            <p className="text-sm text-primary-foreground">{message.content}</p>
          </div>
          <div className="h-8 w-8 flex items-center justify-center rounded-full bg-primary/10 ring-2 ring-primary/20">
            <User className="h-4 w-4 text-primary" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex">
      <div className="flex max-w-[85%] gap-3">
        <div className="h-8 w-8 flex items-center justify-center rounded-full bg-muted ring-2 ring-border">
          <Bot className="h-4 w-4 text-muted-foreground" />
        </div>
        <div className="rounded-2xl rounded-tl-md bg-muted/50 px-4 py-3 border border-border/50">
          <div className="prose prose-sm dark:prose-invert prose-p:text-foreground prose-headings:text-foreground prose-strong:text-foreground">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}
