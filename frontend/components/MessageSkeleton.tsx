import { Bot } from "lucide-react";

export function MessageSkeleton() {
  return (
    <div className="flex items-start gap-3 sm:gap-4">
      {/* Avatar with Bot icon */}
      <div className="flex-shrink-0">
        <div className="h-8 w-8 sm:h-10 sm:w-10 flex items-center justify-center rounded-full bg-muted ring-2 ring-border">
          <Bot className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
        </div>
      </div>

      {/* Content skeleton */}
      <div className="flex-1 space-y-3 pt-1">
        {/* Thinking text */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-sm text-muted-foreground font-medium">
            Thinking
          </span>
          <div className="flex gap-1">
            <div
              className="h-1.5 w-1.5 rounded-full bg-primary/40 animate-bounce"
              style={{ animationDelay: "0ms" }}
            />
            <div
              className="h-1.5 w-1.5 rounded-full bg-primary/40 animate-bounce"
              style={{ animationDelay: "150ms" }}
            />
            <div
              className="h-1.5 w-1.5 rounded-full bg-primary/40 animate-bounce"
              style={{ animationDelay: "300ms" }}
            />
          </div>
        </div>

        {/* Line 1 - 90% width */}
        <div
          className="h-4 bg-muted/50 rounded-md animate-pulse"
          style={{ width: "90%" }}
        />

        {/* Line 2 - 75% width */}
        <div
          className="h-4 bg-muted/50 rounded-md animate-pulse"
          style={{ width: "75%" }}
        />

        {/* Line 3 - 85% width */}
        <div
          className="h-4 bg-muted/50 rounded-md animate-pulse"
          style={{ width: "85%" }}
        />
      </div>
    </div>
  );
}
