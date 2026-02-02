"use client";

import { useState } from "react";
import { Lock, Shield } from "lucide-react";

interface LoginModalProps {
  isOpen: boolean;
  onLogin: (key: string) => void;
}

export function LoginModal({ isOpen, onLogin }: LoginModalProps) {
  const [authKey, setAuthKey] = useState("");
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!authKey.trim()) {
      setError("Please enter an authentication key");
      return;
    }
    onLogin(authKey);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-md mx-4 bg-background rounded-2xl shadow-2xl border border-border">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/5 border border-primary/10">
              <Shield className="w-5 h-5 text-primary" />
            </div>
            <h2 className="text-xl font-semibold tracking-tight text-foreground">
              Authentication Required
            </h2>
          </div>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-4 bg-muted rounded-xl border border-border">
            <p className="text-sm text-muted-foreground">
              {" "}
              A basic authentication just to prevent abuse of the API Keys.
            </p>
          </div>

          <div>
            <label
              htmlFor="authKey"
              className="block text-sm font-medium text-foreground mb-2"
            >
              Authentication Key
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-muted-foreground" />
              </div>
              <input
                type="password"
                id="authKey"
                value={authKey}
                onChange={(e) => {
                  setAuthKey(e.target.value);
                  setError("");
                }}
                className="block w-full pl-10 pr-4 py-3 rounded-xl border border-input
                         bg-card text-foreground
                         placeholder:text-muted-foreground
                         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
                         transition-colors"
                placeholder="Enter your authentication key"
                autoFocus
              />
            </div>
            {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
          </div>

          <button
            type="submit"
            className="w-full py-3 px-4 bg-primary hover:bg-primary/90
                     text-primary-foreground font-medium rounded-xl
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
                     transition-colors duration-200 shadow-sm hover:shadow"
          >
            Continue
          </button>
        </form>
      </div>
    </div>
  );
}
