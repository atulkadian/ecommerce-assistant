"use client";

import { useState, useRef, useEffect } from "react";
import { Message } from "@/types/chat";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { LoadingIndicator } from "@/components/LoadingIndicator";
import { ShoppingCart, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { ThemeToggle } from "@/components/theme-toggle";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      role: "user",
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const history = messages
        .filter((msg) => msg.role !== "system")
        .map((msg) => ({ role: msg.role, content: msg.content }));

      const response = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          conversation_history: history,
        }),
      });

      if (!response.ok) throw new Error("Failed to get response");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              try {
                const parsed = JSON.parse(data);
                if (parsed.content && !parsed.done) {
                  assistantMessage += parsed.content;
                  if (isLoading) setIsLoading(false);

                  setMessages((prev) => {
                    const last = prev[prev.length - 1];
                    if (
                      last?.role === "assistant" &&
                      last.timestamp > userMessage.timestamp
                    ) {
                      return [
                        ...prev.slice(0, -1),
                        { ...last, content: assistantMessage },
                      ];
                    }
                    return [
                      ...prev,
                      {
                        role: "assistant",
                        content: assistantMessage,
                        timestamp: new Date(),
                      },
                    ];
                  });
                }
              } catch (e) {}
            } else if (line.startsWith("event: error")) {
              const idx = lines.indexOf(line) + 1;
              if (idx < lines.length && lines[idx].startsWith("data: ")) {
                try {
                  const { type, error } = JSON.parse(lines[idx].slice(6));
                  const title =
                    type === "quota_error"
                      ? "API Quota Exceeded"
                      : type === "auth_error"
                        ? "Auth Error"
                        : "Error";
                  toast.error(title, {
                    description: error || "An error occurred",
                    duration: 5000,
                  });
                } catch (e) {}
              }
            }
          }
        }
      }
    } catch (error) {
      toast.error("Connection Error", {
        description: "Failed to connect. Try again.",
        duration: 4000,
      });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, something went wrong. Try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-xl">
        <div className="flex h-14 items-center justify-between px-4 mx-auto max-w-5xl">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <ShoppingCart className="h-4 w-4 text-primary" />
            </div>
            <h1 className="text-base font-semibold">Shopping Assistant</h1>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-4 py-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[70vh] space-y-8">
              <div className="flex flex-col items-center space-y-4 text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 ring-1 ring-primary/10">
                  <ShoppingCart className="h-7 w-7 text-primary" />
                </div>
                <h2 className="text-xl font-semibold">Shopping Assistant</h2>
                <p className="text-sm text-muted-foreground max-w-sm">
                  Discover products and find what you're looking for
                </p>
              </div>

              <div className="grid sm:grid-cols-2 gap-3 w-full max-w-xl">
                {[
                  "Show me products under $50",
                  "What electronics are available?",
                  "Find men's clothing",
                  "Show me jewelry",
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSendMessage(prompt)}
                    disabled={isLoading}
                    className="group rounded-xl border border-border/50 bg-card/50 p-4 text-left text-sm hover:bg-accent disabled:opacity-50"
                  >
                    <div className="flex gap-3">
                      <Sparkles className="h-4 w-4 mt-0.5 text-muted-foreground group-hover:text-primary" />
                      <span>{prompt}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} />
              ))}
              {isLoading && <LoadingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      <div className="border-t bg-background/80 backdrop-blur-xl">
        <div className="mx-auto max-w-4xl px-4 py-4">
          <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>
      </div>
    </main>
  );
}
