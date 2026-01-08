"use client";

import React, { RefObject } from "react";
import { ChatMessage as TypesChatMessage } from "@/lib/types";
import { ChatMessage as ApiChatMessage } from "@/lib/api-client";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Loader2, Sparkles, ArrowDown, Cloud, Newspaper, Train, ImageIcon, Star, Languages } from "lucide-react";
import { MessageBubble } from "./MessageBubble";

type ChatAreaProps = {
  messages: TypesChatMessage[];
  currentAIMessage: string;
  isFetchingMessages: boolean;
  userInitials: string;
  inputRef: RefObject<HTMLTextAreaElement | null>;
  chatAreaRef: RefObject<HTMLDivElement | null>;
  messagesEndRef: RefObject<HTMLDivElement | null>;
  isScrolledToBottom: boolean;
  onSuggestionSelect: (text: string) => void;
  onScrollToBottom: () => void;
  onRegenerate?: () => void;
  onFeedback?: (messageId: string, feedback: "up" | "down") => void;
};

const suggestions = [
  { icon: Cloud, text: "What's the weather in Delhi?", color: "from-cyan-500 to-blue-500" },
  { icon: Newspaper, text: "Show me today's top news", color: "from-orange-500 to-red-500" },
  { icon: Train, text: "Check PNR 2827599631", color: "from-green-500 to-emerald-500" },
  { icon: ImageIcon, text: "Create an image of a sunset", color: "from-pink-500 to-rose-500" },
  { icon: Star, text: "My horoscope for Aries", color: "from-violet-500 to-purple-500" },
  { icon: Languages, text: "Translate 'hello' to Hindi", color: "from-amber-500 to-yellow-500" },
];

export function ChatArea({
  messages,
  currentAIMessage,
  isFetchingMessages,
  userInitials,
  inputRef,
  chatAreaRef,
  messagesEndRef,
  isScrolledToBottom,
  onSuggestionSelect,
  onScrollToBottom,
  onRegenerate,
  onFeedback,
}: ChatAreaProps) {
  const showEmptyState = messages.length === 0 && !currentAIMessage;

  if (showEmptyState) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-8">
        <div className="max-w-2xl w-full text-center space-y-8">
          {/* Logo & Welcome */}
          <div className="space-y-4">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-lg shadow-violet-500/25">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                How can I help you today?
              </h1>
              <p className="text-zinc-400 text-sm">
                Ask me about weather, news, train status, horoscopes, or anything else
              </p>
            </div>
          </div>

          {/* Suggestion Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {suggestions.map((suggestion, i) => {
              const Icon = suggestion.icon;
              return (
                <button
                  key={i}
                  className="group flex flex-col items-start gap-3 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800/50 transition-all text-left"
                  onClick={() => {
                    onSuggestionSelect(suggestion.text);
                    inputRef.current?.focus();
                  }}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br ${suggestion.color} shadow-lg`}>
                    <Icon className="h-5 w-5 text-white" />
                  </div>
                  <span className="text-sm text-zinc-300 group-hover:text-white transition-colors leading-tight">
                    {suggestion.text}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // Convert messages to the format expected by MessageBubble
  const formattedMessages: ApiChatMessage[] = messages.map(msg => ({
    id: msg.id,
    role: msg.role as "user" | "assistant",
    content: msg.content,
    timestamp: msg.created_at || new Date().toISOString(),
    language: "en",
    media_url: msg.media_url,
    intent: msg.intent,
    structured_data: msg.structured_data,
  }));

  return (
    <div className="flex-1 overflow-hidden flex flex-col relative h-full">
      <ScrollArea ref={chatAreaRef} className="flex-1 h-full [&>[data-slot=scroll-area-viewport]]:h-full [&>[data-slot=scroll-area-viewport]]:max-h-full">
        <div className="max-w-3xl mx-auto px-4 py-6">
          {isFetchingMessages ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-violet-400" />
            </div>
          ) : (
            formattedMessages.map((msg, idx) => {
              // Find the last assistant message index
              const lastAssistantIdx = formattedMessages.reduce(
                (lastIdx, m, i) => (m.role === "assistant" ? i : lastIdx),
                -1
              );
              const isLastAssistant = msg.role === "assistant" && idx === lastAssistantIdx;

              return (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  isLastAssistantMessage={isLastAssistant}
                  onRegenerate={isLastAssistant ? onRegenerate : undefined}
                  onFeedback={onFeedback}
                />
              );
            })
          )}

          {/* Streaming AI message */}
          {currentAIMessage && (
            <MessageBubble
              message={{
                id: "streaming",
                role: "assistant",
                content: currentAIMessage,
                timestamp: new Date().toISOString(),
                language: "en",
              }}
            />
          )}

          {/* Typing indicator when waiting for response */}
          {currentAIMessage === "" && messages.length > 0 && messages[messages.length - 1]?.role === "user" && (
            <div className="flex gap-3 mb-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-violet-400" />
              </div>
              <div className="flex items-center gap-1 px-4 py-3 rounded-2xl bg-muted rounded-tl-sm">
                <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Scroll to bottom button */}
      {!isScrolledToBottom && (
        <div className="absolute right-6 bottom-4">
          <Button
            size="icon"
            onClick={onScrollToBottom}
            className="rounded-full shadow-lg bg-zinc-800 hover:bg-zinc-700 border border-zinc-700"
          >
            <ArrowDown className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
