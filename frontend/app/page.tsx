"use client";

import { useState, useRef, useEffect } from "react";
import { Message } from "@/types/chat";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { MessageSkeleton } from "@/components/MessageSkeleton";
import { Sidebar } from "@/components/Sidebar";
import { Snowfall } from "@/components/Snowfall";
import { ShoppingCart, Sparkles, Menu } from "lucide-react";
import { toast } from "sonner";
import { ThemeToggle } from "@/components/theme-toggle";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<
    number | null
  >(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [refreshSidebar, setRefreshSidebar] = useState(0);
  const [snowEnabled, setSnowEnabled] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleResize = () => {
      setIsSidebarOpen(window.innerWidth >= 1024);
    };

    handleResize();

    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadConversation = async (id: number) => {
    try {
      const res = await fetch(`${API_URL}/conversations/${id}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(
          data.messages.map((msg: any) => ({
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp),
          })),
        );
        setCurrentConversationId(id);
      }
    } catch (error) {
      toast.error("Failed to load conversation");
    }
  };

  const handleSelectConversation = (id: number | null) => {
    if (id === null) {
      setMessages([]);
      setCurrentConversationId(null);
    } else {
      loadConversation(id);
    }
  };

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
          conversation_id: currentConversationId,
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
                } else if (parsed.done && parsed.conversation_id) {
                  // Update conversation ID and refresh sidebar
                  if (!currentConversationId) {
                    setCurrentConversationId(parsed.conversation_id);
                    setRefreshSidebar((prev) => prev + 1);
                  }
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
      <Snowfall enabled={snowEnabled} />

      <Sidebar
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        isOpen={isSidebarOpen}
        setIsOpen={setIsSidebarOpen}
        refreshTrigger={refreshSidebar}
        snowEnabled={snowEnabled}
        setSnowEnabled={setSnowEnabled}
      />

      {/* Header */}
      <header
        className={`sticky top-0 z-20 border-b border-border bg-card/95 backdrop-blur-xl transition-all duration-300 shadow-sm ${
          isSidebarOpen ? "lg:ml-72" : ""
        }`}
      >
        <div className="flex h-16 items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2 sm:gap-4">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 hover:bg-accent rounded-lg transition-colors border border-transparent hover:border-border"
              aria-label="Toggle sidebar"
            >
              <Menu className="h-5 w-5 text-foreground" />
            </button>
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="flex h-8 w-8 sm:h-10 sm:w-10 items-center justify-center rounded-xl bg-primary/5 border border-primary/10">
                <ShoppingCart className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-base font-semibold tracking-tight text-foreground">
                  Shopping Assistant
                </h1>
                <p className="text-xs text-muted-foreground">
                  AI-powered product discovery
                </p>
              </div>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Main Content */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          isSidebarOpen ? "lg:ml-72" : ""
        }`}
      >
        {messages.length === 0 ? (
          <>
            <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-8">
              <div className="flex flex-col items-center space-y-4 sm:space-y-5 text-center mb-8 sm:mb-10">
                <div className="flex h-12 w-12 sm:h-16 sm:w-16 items-center justify-center rounded-2xl bg-primary/5 border border-primary/10 shadow-sm">
                  <ShoppingCart className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-xl sm:text-2xl font-semibold tracking-tight">
                    Shopping Assistant
                  </h2>
                  <p className="text-xs sm:text-sm text-muted-foreground max-w-md px-4">
                    Discover products and find exactly what you're looking for
                    with AI-powered assistance
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 w-full max-w-2xl mb-8 sm:mb-12">
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
                    className="group rounded-xl border border-border bg-card p-3 sm:p-4 text-left text-sm hover:bg-accent hover:shadow-sm disabled:opacity-50 transition-all"
                  >
                    <div className="flex gap-2 sm:gap-3">
                      <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground group-hover:text-foreground transition-colors" />
                      <span className="text-foreground/90 group-hover:text-foreground">
                        {prompt}
                      </span>
                    </div>
                  </button>
                ))}
              </div>

              {/* Input Area - Centered below suggestions */}
              <div className="w-full max-w-4xl px-4 sm:px-6">
                <ChatInput
                  onSendMessage={handleSendMessage}
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Footer - Fixed at bottom */}
            <div className="bg-card/95 backdrop-blur-xl border-t border-border">
              <div className="mx-auto max-w-4xl px-4 sm:px-6 py-3 sm:py-4">
                <div className="text-center text-xs text-muted-foreground">
                  Crafted by Atul Kadian
                  {" • "}
                  <a
                    href="https://github.com/atulkadian"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-foreground transition-colors"
                  >
                    GitHub
                  </a>
                  {" • "}
                  <a
                    href="https://www.linkedin.com/in/atul-kadian/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-foreground transition-colors"
                  >
                    LinkedIn
                  </a>
                </div>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto">
              <div className="mx-auto max-w-4xl px-4 sm:px-6 py-6 sm:py-8">
                <div className="space-y-4 sm:space-y-6">
                  {messages.map((msg, i) => (
                    <ChatMessage key={i} message={msg} />
                  ))}
                  {isLoading && <MessageSkeleton />}
                  <div ref={messagesEndRef} />
                </div>
              </div>
            </div>

            {/* Input Area - Fixed at bottom when messages exist */}
            <div className="bg-card/95 backdrop-blur-xl">
              <div className="mx-auto max-w-4xl px-4 sm:px-6 py-3 sm:py-4">
                <ChatInput
                  onSendMessage={handleSendMessage}
                  disabled={isLoading}
                />
                <div className="text-center mt-2 sm:mt-3 text-xs text-muted-foreground">
                  Crafted by{" "}
                  <a
                    href="https://www.linkedin.com/in/atul-kadian/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium hover:text-foreground transition-colors"
                  >
                    Atul Kadian
                  </a>
                  {" • "}
                  <a
                    href="https://github.com/atulkadian"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-foreground transition-colors"
                  >
                    GitHub
                  </a>
                  {" • "}
                  <a
                    href="https://www.linkedin.com/in/atul-kadian/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-foreground transition-colors"
                  >
                    LinkedIn
                  </a>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
