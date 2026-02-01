export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
}

export interface ChatRequest {
  message: string;
  conversation_history?: Array<{
    role: string;
    content: string;
  }>;
}
