"use client";

import { useState, useEffect } from "react";
import { Plus, Trash2, MessageSquare, X, Snowflake } from "lucide-react";

interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

interface SidebarProps {
  currentConversationId: number | null;
  onSelectConversation: (id: number | null) => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  refreshTrigger?: number;
  snowEnabled: boolean;
  setSnowEnabled: (enabled: boolean) => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function Sidebar({
  currentConversationId,
  onSelectConversation,
  isOpen,
  setIsOpen,
  refreshTrigger,
  snowEnabled,
  setSnowEnabled,
}: SidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  const loadConversations = async () => {
    try {
      const res = await fetch(`${API_URL}/conversations`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      loadConversations();
    }
  }, [refreshTrigger]);

  const createNewConversation = async () => {
    // Just clear the current conversation to start a new one
    onSelectConversation(null);
    // Close sidebar on mobile
    if (window.innerWidth < 1024) {
      setIsOpen(false);
    }
  };

  const deleteConversation = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await fetch(`${API_URL}/conversations/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setConversations(conversations.filter((c) => c.id !== id));
        if (currentConversationId === id) {
          onSelectConversation(null);
        }
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    }
  };

  const handleSelectConversation = (id: number) => {
    onSelectConversation(id);
    // Close sidebar on mobile
    if (window.innerWidth < 1024) {
      setIsOpen(false);
    }
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full w-72 bg-background border-r border-border flex flex-col z-40 transition-transform duration-300 ease-in-out shadow-lg ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 h-16 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/5 border border-primary/10">
              <MessageSquare className="h-4 w-4 text-primary" />
            </div>
            <h2 className="font-semibold text-sm tracking-tight">
              Conversations
            </h2>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="lg:hidden p-2 hover:bg-accent rounded-lg transition-colors"
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={createNewConversation}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all font-medium text-sm shadow-sm hover:shadow"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 scrollbar-thin">
          {conversations.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground mt-12">
              <p className="font-medium">No conversations yet</p>
              <p className="text-xs mt-1">Start a new chat to begin</p>
            </div>
          ) : (
            <div className="space-y-1.5">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv.id)}
                  className={`group relative flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                    currentConversationId === conv.id
                      ? "bg-accent border border-border shadow-sm"
                      : "hover:bg-accent/50 border border-transparent"
                  }`}
                >
                  <MessageSquare
                    className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                      currentConversationId === conv.id
                        ? "text-foreground"
                        : "text-muted-foreground"
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm font-medium truncate ${
                        currentConversationId === conv.id
                          ? "text-foreground"
                          : "text-foreground/90"
                      }`}
                    >
                      {conv.title}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {new Date(conv.updated_at).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </p>
                  </div>
                  <button
                    onClick={(e) => deleteConversation(conv.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-destructive/10 rounded-md transition-all flex-shrink-0"
                    aria-label="Delete conversation"
                  >
                    <Trash2 className="h-3.5 w-3.5 text-destructive" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer with Snow Toggle */}
        <div className="border-t border-border">
          <div className="px-4 py-3">
            <button
              onClick={() => setSnowEnabled(!snowEnabled)}
              className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg transition-all font-medium text-sm ${
                snowEnabled
                  ? "bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20 border border-blue-500/20"
                  : "bg-muted text-muted-foreground hover:bg-accent border border-border"
              }`}
            >
              <Snowflake
                className={`h-4 w-4 ${snowEnabled ? "animate-spin" : ""}`}
              />
              {snowEnabled ? "Snow Enabled" : "Let it Snow"}
            </button>
          </div>
          <div className="px-4 pb-3">
            <p className="text-xs text-muted-foreground text-center">
              {conversations.length} conversation
              {conversations.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
