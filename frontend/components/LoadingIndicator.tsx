import { Loader2 } from "lucide-react";

export function LoadingIndicator() {
  return (
    <div className="flex gap-3 p-4 rounded-lg bg-secondary/50">
      <div className="h-8 w-8 flex items-center justify-center rounded-md bg-muted">
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium">Shopping Assistant</p>
        <p className="text-sm text-muted-foreground">Thinking...</p>
      </div>
    </div>
  );
}
