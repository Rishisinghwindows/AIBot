"use client";

import { useState, useCallback, useEffect } from "react";
import { cn } from "@/lib/utils";
import { ChatMessage } from "@/lib/api-client";
import { User, Bot, Copy, Check, ThumbsUp, ThumbsDown, RefreshCw } from "lucide-react";
import { PNRCard, WeatherCard, HoroscopeCard, TarotCard, NewsCard, NumerologyCard } from "./cards";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface MessageBubbleProps {
  message: ChatMessage;
  isLastAssistantMessage?: boolean;
  onRegenerate?: () => void;
  onFeedback?: (messageId: string, feedback: "up" | "down") => void;
}

export function MessageBubble({
  message,
  isLastAssistantMessage = false,
  onRegenerate,
  onFeedback
}: MessageBubbleProps) {
  const isUser = message.role === "user";
  const timestamp = new Date(message.timestamp);
  const [imageError, setImageError] = useState(false);
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  // Reset imageError when media_url changes
  useEffect(() => {
    setImageError(false);
  }, [message.media_url]);

  // Copy message to clipboard
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  }, [message.content]);

  // Handle feedback
  const handleFeedback = useCallback((type: "up" | "down") => {
    setFeedback(type);
    onFeedback?.(message.id, type);
  }, [message.id, onFeedback]);

  // Check if we should render a rich card
  const shouldRenderCard = !isUser && message.intent && message.structured_data;

  // Render the appropriate card based on intent
  const renderRichCard = () => {
    if (!message.structured_data) return null;

    switch (message.intent) {
      case "pnr_status":
        return <PNRCard data={message.structured_data as any} />;
      case "weather":
      case "get_weather":
        return <WeatherCard data={message.structured_data as any} />;
      case "get_horoscope":
      case "horoscope":
        return <HoroscopeCard data={message.structured_data as any} />;
      case "tarot_reading":
      case "tarot":
        return <TarotCard data={message.structured_data as any} />;
      case "get_news":
      case "news":
        const newsData = message.structured_data as any;
        return <NewsCard items={newsData.articles || newsData.items || [newsData]} />;
      case "numerology":
        return <NumerologyCard data={message.structured_data as any} />;
      default:
        return null;
    }
  };

  const richCard = shouldRenderCard ? renderRichCard() : null;

  return (
    <div
      className={cn(
        "group flex gap-3 max-w-[85%] mb-4",
        isUser ? "ml-auto flex-row-reverse" : "mr-auto"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground"
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message Content */}
      <div
        className={cn(
          "flex flex-col",
          isUser ? "items-end" : "items-start"
        )}
      >
        {/* Rich Card (if available) */}
        {richCard && (
          <div className="mb-2 w-full max-w-md">
            {richCard}
          </div>
        )}

        {/* Text Message (only show if no rich card - cards contain all the info) */}
        {!richCard && (
          <div
            className={cn(
              "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
              isUser
                ? "bg-primary text-primary-foreground rounded-tr-sm"
                : "bg-muted text-foreground rounded-tl-sm"
            )}
          >
            {/* Render message with line breaks and code highlighting */}
            <div className="whitespace-pre-wrap break-words">
              <FormattedMessage content={message.content} />
            </div>

            {/* Render image if media_url is present */}
            {message.media_url && (
              <div className="mt-2">
                {imageError ? (
                  <div className="text-xs text-destructive p-2 bg-destructive/10 rounded">
                    Image failed to load. <a href={message.media_url} target="_blank" rel="noopener noreferrer" className="underline">Open in new tab</a>
                  </div>
                ) : (
                  <a href={message.media_url} target="_blank" rel="noopener noreferrer">
                    <img
                      src={message.media_url}
                      alt="Generated image"
                      className="rounded-lg max-w-full h-auto cursor-pointer hover:opacity-90 transition-opacity"
                      style={{ maxHeight: '300px' }}
                      referrerPolicy="no-referrer"
                      onError={() => setImageError(true)}
                      loading="eager"
                    />
                  </a>
                )}
              </div>
            )}
          </div>
        )}

        {/* Timestamp and Actions */}
        <div className="flex items-center gap-2 mt-1 px-1">
          <span className="text-[10px] text-muted-foreground">
            {formatTime(timestamp)}
          </span>

          {/* Action buttons for assistant messages */}
          {!isUser && message.id !== "streaming" && (
            <TooltipProvider delayDuration={300}>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {/* Copy button */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={handleCopy}
                      className="p-1 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
                    >
                      {copied ? (
                        <Check className="w-3.5 h-3.5 text-green-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p>{copied ? "Copied!" : "Copy message"}</p>
                  </TooltipContent>
                </Tooltip>

                {/* Regenerate button (only for last assistant message) */}
                {isLastAssistantMessage && onRegenerate && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={onRegenerate}
                        className="p-1 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p>Regenerate response</p>
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Feedback buttons */}
                <div className="flex items-center gap-0.5 ml-1 border-l border-zinc-800 pl-1">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => handleFeedback("up")}
                        className={cn(
                          "p-1 rounded transition-colors",
                          feedback === "up"
                            ? "text-green-400 bg-green-400/10"
                            : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800"
                        )}
                      >
                        <ThumbsUp className="w-3.5 h-3.5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p>Good response</p>
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => handleFeedback("down")}
                        className={cn(
                          "p-1 rounded transition-colors",
                          feedback === "down"
                            ? "text-red-400 bg-red-400/10"
                            : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800"
                        )}
                      >
                        <ThumbsDown className="w-3.5 h-3.5" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom">
                      <p>Bad response</p>
                    </TooltipContent>
                  </Tooltip>
                </div>
              </div>
            </TooltipProvider>
          )}
        </div>
      </div>
    </div>
  );
}

// Component to render formatted message with code blocks
function FormattedMessage({ content }: { content: string }) {
  // Parse the message for code blocks and inline code
  const parts: Array<{ type: "text" | "code-block" | "inline-code"; content: string; language?: string }> = [];
  let remaining = content;

  // Match code blocks first (```language\ncode```)
  const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    // Add text before this code block
    if (match.index > lastIndex) {
      parts.push({
        type: "text",
        content: content.slice(lastIndex, match.index)
      });
    }

    // Add the code block
    parts.push({
      type: "code-block",
      language: match[1] || "plaintext",
      content: match[2].trim()
    });

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < content.length) {
    parts.push({
      type: "text",
      content: content.slice(lastIndex)
    });
  }

  // If no code blocks found, check for inline code
  if (parts.length === 0 || (parts.length === 1 && parts[0].type === "text")) {
    const textContent = parts.length === 1 ? parts[0].content : content;
    const inlineParts: Array<{ type: "text" | "inline-code"; content: string }> = [];
    const inlineCodeRegex = /`([^`]+)`/g;
    let inlineLastIndex = 0;
    let inlineMatch;

    while ((inlineMatch = inlineCodeRegex.exec(textContent)) !== null) {
      if (inlineMatch.index > inlineLastIndex) {
        inlineParts.push({
          type: "text",
          content: textContent.slice(inlineLastIndex, inlineMatch.index)
        });
      }
      inlineParts.push({
        type: "inline-code",
        content: inlineMatch[1]
      });
      inlineLastIndex = inlineMatch.index + inlineMatch[0].length;
    }

    if (inlineLastIndex < textContent.length) {
      inlineParts.push({
        type: "text",
        content: textContent.slice(inlineLastIndex)
      });
    }

    if (inlineParts.length > 1) {
      return (
        <>
          {inlineParts.map((part, i) =>
            part.type === "inline-code" ? (
              <code
                key={i}
                className="px-1.5 py-0.5 rounded bg-zinc-800 text-violet-300 text-xs font-mono"
              >
                {part.content}
              </code>
            ) : (
              <span key={i}>{formatText(part.content)}</span>
            )
          )}
        </>
      );
    }
  }

  // Render parts
  if (parts.length === 0) {
    return <>{formatText(content)}</>;
  }

  return (
    <>
      {parts.map((part, i) => {
        if (part.type === "code-block") {
          return (
            <div key={i} className="my-2 rounded-lg overflow-hidden bg-zinc-900 border border-zinc-800">
              <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-800/50 border-b border-zinc-800">
                <span className="text-xs text-zinc-500 font-mono">{part.language}</span>
                <CopyCodeButton code={part.content} />
              </div>
              <pre className="p-3 overflow-x-auto">
                <code className="text-xs font-mono text-zinc-300 leading-relaxed">
                  {part.content}
                </code>
              </pre>
            </div>
          );
        }
        return <span key={i}>{formatText(part.content)}</span>;
      })}
    </>
  );
}

// Copy button for code blocks
function CopyCodeButton({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="p-1 rounded hover:bg-zinc-700 text-zinc-500 hover:text-zinc-300 transition-colors"
    >
      {copied ? (
        <Check className="w-3 h-3 text-green-400" />
      ) : (
        <Copy className="w-3 h-3" />
      )}
    </button>
  );
}

function formatText(content: string): string {
  // Convert WhatsApp-style bold markers to clean text for display
  // The rich cards handle the formatting, so we just clean up the text
  return content.replace(/\*([^*]+)\*/g, "$1");
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}
