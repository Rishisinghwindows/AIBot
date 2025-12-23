"use client";

import { useState, useEffect, useRef } from "react";
import { apiClient, ChatMessage, WebSession } from "@/lib/api-client";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { Button } from "@/components/ui/button";
import { Trash2, RotateCcw, MessageCircle, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

// Suggested prompts for new users - showcasing all tools
const SUGGESTED_PROMPTS = [
  // Core Features
  { icon: "cloud", text: "Weather in Mumbai today", category: "Weather" },
  { icon: "newspaper", text: "Today's top news India", category: "News" },
  { icon: "train", text: "PNR status 2124567890", category: "PNR" },
  { icon: "image", text: "Generate image of Taj Mahal at sunset", category: "Image" },
  // Astrology Features
  { icon: "star", text: "Aries horoscope for today", category: "Horoscope" },
  { icon: "sparkles", text: "Numerology for DOB 15 May 1990", category: "Numerology" },
  { icon: "moon", text: "Today's Panchang", category: "Panchang" },
  { icon: "heart", text: "Tarot reading for love", category: "Tarot" },
];

export function ChatContainer() {
  const [session, setSession] = useState<WebSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize session on mount
  useEffect(() => {
    initSession();
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initSession = async () => {
    setIsInitializing(true);
    setError(null);

    try {
      const sess = await apiClient.getOrCreateSession();
      setSession(sess);

      // Load chat history
      try {
        const history = await apiClient.getChatHistory(sess.session_id);
        setMessages(history.messages);
      } catch {
        // No history, start fresh
        setMessages([]);
      }
    } catch (err) {
      setError("Failed to connect. Please refresh the page.");
      console.error("Session init error:", err);
    } finally {
      setIsInitializing(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSendMessage = async (text: string) => {
    if (!session || isLoading) return;

    setIsLoading(true);
    setError(null);

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
      language: session.language,
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await apiClient.sendMessage(session.session_id, text);

      // Debug: log the assistant message to check media_url
      console.log("[ChatContainer] Assistant message:", response.assistant_message);
      console.log("[ChatContainer] Media URL:", response.assistant_message?.media_url);

      // Replace temp message with actual messages
      setMessages((prev) => {
        const newMessages = [
          ...prev.filter((m) => m.id !== tempUserMsg.id),
          response.user_message,
          response.assistant_message,
        ];
        console.log("[ChatContainer] New messages array:", newMessages.map(m => ({id: m.id, media_url: m.media_url})));
        return newMessages;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
      // Remove temp message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = async () => {
    if (!session) return;

    try {
      await apiClient.deleteSession(session.session_id);
      setMessages([]);
      // Create new session
      await initSession();
    } catch (err) {
      setError("Failed to clear chat");
      console.error("Clear chat error:", err);
    }
  };

  const handlePromptClick = (prompt: string) => {
    handleSendMessage(prompt);
  };

  // Loading state
  if (isInitializing) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <div className="animate-pulse">
          <MessageCircle className="w-12 h-12 text-primary" />
        </div>
        <p className="text-muted-foreground">Connecting...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-primary-foreground" />
          </div>
          <div>
            <h2 className="font-semibold text-sm">D23 AI Assistant</h2>
            <p className="text-[10px] text-muted-foreground">
              Always here to help
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClearChat}
            title="Clear chat"
            className="h-8 w-8"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Messages Area */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 space-y-1"
      >
        {messages.length === 0 ? (
          <EmptyState onPromptClick={handlePromptClick} />
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Typing indicator */}
            {isLoading && (
              <div className="flex gap-3 max-w-[85%] mb-4">
                <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-4 h-4 text-muted-foreground" />
                </div>
                <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3">
                  <TypingIndicator />
                </div>
              </div>
            )}
          </>
        )}

        {/* Error message */}
        {error && (
          <div className="flex items-center justify-center gap-2 py-2 px-4 mx-auto max-w-md bg-destructive/10 text-destructive rounded-lg text-sm">
            <span>{error}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setError(null)}
              className="h-6 px-2"
            >
              <RotateCcw className="h-3 w-3" />
            </Button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <ChatInput
        onSend={handleSendMessage}
        isLoading={isLoading}
        placeholder="Ask me anything..."
        disabled={!session}
      />
    </div>
  );
}

// Empty state with suggested prompts
function EmptyState({ onPromptClick }: { onPromptClick: (prompt: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-8 px-4">
      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-4">
        <Sparkles className="w-8 h-8 text-primary" />
      </div>

      <h3 className="text-lg font-semibold mb-1">Welcome to D23 AI</h3>
      <p className="text-muted-foreground text-sm text-center mb-6 max-w-sm">
        Your AI assistant for astrology, weather, news, travel, and more.
        Available in 22 Indian languages.
      </p>

      <div className="w-full max-w-md">
        <p className="text-xs text-muted-foreground mb-3 text-center">
          Try asking:
        </p>
        <div className="grid grid-cols-2 gap-2">
          {SUGGESTED_PROMPTS.map((prompt, i) => (
            <button
              key={i}
              onClick={() => onPromptClick(prompt.text)}
              className={cn(
                "flex flex-col items-start p-3 rounded-xl",
                "bg-muted/50 hover:bg-muted transition-colors",
                "text-left text-sm"
              )}
            >
              <span className="text-[10px] text-muted-foreground mb-0.5">
                {prompt.category}
              </span>
              <span className="text-foreground line-clamp-2">
                {prompt.text}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// Typing indicator dots
function TypingIndicator() {
  return (
    <div className="flex gap-1">
      <div className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:-0.3s]" />
      <div className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:-0.15s]" />
      <div className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" />
    </div>
  );
}
